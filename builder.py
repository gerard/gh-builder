#!/usr/bin/env python
import socket
import urllib2
import json
import re
import os
import sys
import subprocess
import struct
import shutil
import datetime

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("192.168.1.64", 8765))
s.listen(5)

CONFIG = {
    'allowed_users':    ["AndroidAalto", "mkd", "marcostong17", "mataanin", "gerard", "quelcom", "jush", "hleinone"],
    'builder_root':     "/home/gerard/builder",
    'git_cmd':          "git",
    'workspace_dir':    "_workspace",
}

try:
    __log_file = open(sys.argv[1], "a")
except:
    __log_file = None
    print "W: No log file open"
    pass

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

while 1:
    (client_s, _) = s.accept()
    client_s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('LL', 2, 0))
    data = ""

    info("New connection incoming")
    while 1:
        try:
            more = client_s.recv(4096)
        except socket.error: # This triggers because of SO_RCVTIMEO
            break
        data += more
        if not more: break
    client_s.close()
    info("Connection closed")

    for m in re.finditer("payload=(.*)", data):
        json_string = urllib2.unquote(m.group(1))
        url = json.loads(json_string)['compare']

    # We only handle the last url for now
    info("Processing URL: %s" % url)
    m = re.match("https://github.com/([A-Za-z0-9_]*)/([A-Za-z0-9_]*)/compare/([0-9a-f]*)\.\.\.([0-9a-f]*)", url)

    (user, repo, fro, to) = (m.group(1), m.group(2), m.group(3), m.group(4))

    if user not in CONFIG["allowed_users"]:
        error("User not allowed: %s" % user)
        continue

    # uid uniquely identifies this build
    repo_dir = CONFIG["builder_root"] + os.sep + user + os.sep + repo
    uid = get_timestamp() + "-" + to

    shutil.rmtree(repo_dir + os.sep + CONFIG["workspace_dir"], True)
    try:
        os.makedirs(repo_dir)
    except OSError:
        pass
    os.chdir(repo_dir)

    git_cmdline_clone       = ["git", "clone", "git://github.com/%s/%s.git" % (user, repo), CONFIG["workspace_dir"]]
    git_cmdline_checkout    = ["git", "checkout", to]
    git_logging_clone       = open(uid + ".git-clone.log", "w")
    git_logging_checkout    = open(uid + ".git-checkout.log", "w")
    make_logging            = open(uid + ".make.log", "w")

    subprocess.call(git_cmdline_clone, stdout=git_logging_clone, stderr=subprocess.STDOUT)
    os.chdir(CONFIG["workspace_dir"])

    # We checkout the received git hash to be sure
    subprocess.call(git_cmdline_checkout, stdout=git_logging_checkout, stderr=subprocess.STDOUT)
    subprocess.call("make", stdout=make_logging, stderr=subprocess.STDOUT)

    git_logging_clone.close()
    git_logging_checkout.close()
    make_logging.close()

    os.chdir("..")
    build_apk_name = CONFIG["workspace_dir"] + os.sep + "bin" + os.sep + CONFIG["workspace_dir"] + "-debug.apk"

    try:
        os.rename(build_apk_name, repo + "-" + uid + ".apk")
    except:
        info("No apk found")

    info("All data processed")
