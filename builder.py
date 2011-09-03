#!/usr/bin/env python
import socket
import urllib2
import json
import re
import os
import os.path
import sys
import struct
import shutil
import datetime
import threading
import ghblib.shellrunner
import ghconfig as CONFIG


def __log(logtype, s):
    s = "[ " + str(datetime.datetime.today()) + "] " + logtype + ": " + s
    if __log_file:
        print >> __log_file, s
        __log_file.flush()
    print s

info    = lambda s: __log("I", s)
error   = lambda s: __log("E", s)

def get_timestamp():
    d = datetime.datetime.today()
    return "%d-%02d-%02d_%02d:%02d" % (d.year, d.month, d.day, d.hour, d.minute)

def get_artifact_log(uid, artifact_name):
    return open(os.path.join(CONFIG.logs_dir, uid + "." + artifact_name + ".log"), "w")

def build(name, logfile, timeout):
    try:
        if os.path.exists("AndroidManifest.xml"):
            # Special-case android projects.  That way we avoid makefiles, which,
            # let's face it, are not precisely Web2.0 ;)
            update_project  = ["android", "update", "project", "-n", name, "-p", "."]
            ant_build       = ["ant", "debug"]

            timeout = ghblib.shellrunner.ShellRunner(update_project, logfile).run(timeout)
            timeout = ghblib.shellrunner.ShellRunner(ant_build, logfile).run(timeout)
        else:
            timeout = ghblib.shellrunner.ShellRunner("make", logfile).run(timeout)

    except ghblib.shellrunner.ShellRunnerTimeout as e:
        error("Timeout while running: %s" % e.cmd)
        return False
    except ghblib.shellrunner.ShellRunner as e:
        error("Command failed [%d]: %s" % (e.retval, e.cmd))
        return False

    return True

class BuilderThread(threading.Thread):
    def __init__(self, sock):
        threading.Thread.__init__(self)
        self.sock = sock

    def run(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 2, 0))
        data = ""
        url = ""
        ref = ""

        info("New connection incoming")
        while 1:
            try:
                more = self.sock.recv(4096)
            except socket.error: # This triggers because of SO_RCVTIMEO
                break
            data += more
            if not more: break
        self.sock.close()
        info("Connection closed")

        for m in re.finditer("payload=(.*)", data):
            json_string = urllib2.unquote(m.group(1))
            json_dict = json.loads(json_string)
            url = json_dict['compare']
            ref = json_dict['ref']

        if ref != "refs/heads/master":
            info("Updated branch is not master [%s].  Skipping for now..." % ref)
            return

        # We only handle the last payload if multiple come
        info("Processing URL: %s" % url)
        m = re.match("https://github.com/([A-Za-z0-9_]*)/([A-Za-z0-9_]*)/compare/([0-9a-f]*)\.\.\.([0-9a-f]*)", url)

        if not m:
            error("Invalid URL")
            return

        (user, repo, fro, to) = (m.group(1), m.group(2), m.group(3), m.group(4))

        if user not in CONFIG.allowed_users:
            error("User not allowed: %s" % user)
            return

        if to == "00000000":
            info("User deleted a branch.  Nothing to see here...")
            return

        # uid uniquely identifies this build
        repo_dir = os.path.join(CONFIG.builder_root, user, repo)
        uid = get_timestamp() + "-" + to

        shutil.rmtree(os.path.join(repo_dir, CONFIG.workspace_dir), True)
        try:
            os.makedirs(os.path.join(repo_dir, CONFIG.logs_dir))
        except OSError:
            pass
        os.chdir(repo_dir)

        git_cmdline_clone       = ["git", "clone", "git://github.com/%s/%s.git" % (user, repo), CONFIG.workspace_dir]
        git_cmdline_checkout    = ["git", "checkout", to]

        # TODO: Move this to the ShellRunner class (it's already closing these)
        git_logging_clone       = get_artifact_log(uid, "git-clone")
        git_logging_checkout    = get_artifact_log(uid, "git-checkout")
        build_logging           = get_artifact_log(uid, "build")

        try:
            ghblib.shellrunner.ShellRunner(git_cmdline_clone, git_logging_clone).run(10)
            os.chdir(CONFIG.workspace_dir)
            ghblib.shellrunner.ShellRunner(git_cmdline_checkout, git_logging_checkout).run(10)
        except ShellRunnerTimeout as e:
            error("Timeout while running: %s" % e.cmd)
            return
        except ShellRunnerFailed as e:
            error("Command failed [%d]: %s" % (e.retval, e.cmd))
            return

        if not build(CONFIG.workspace_dir, build_logging, CONFIG.allowed_users[user].max_build_time):
            error("Build failed")
            return

        os.chdir("..")
        build_apk_name = os.path.join(CONFIG.workspace_dir, "bin", CONFIG.workspace_dir + "-debug.apk")
        apk_final_name = repo + "-" + uid + ".apk"

        try:
            os.rename(build_apk_name, apk_final_name)
        except:
            info("No apk found")

        try:
            tmplink = apk_final_name + ".tmplink"
            os.symlink(apk_final_name, tmplink)
            os.rename(tmplink, repo + ".apk")
        except:
            info("Unable to create symlink")

        info("All data processed")


# Main
# Logging file
try:
    __log_file = open(sys.argv[1], "a")
except:
    __log_file = None
    print "W: No log file open"
    pass

# Set up server socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("192.168.1.64", 8765))
s.listen(5)

# Main loop: one loop per accept(2)ed incoming conection
while 1:
    (client_s, _) = s.accept()
    t = BuilderThread(client_s)
    t.start()
    t.join()
