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
}

try:
    __log_file = open(sys.argv[1], "a")
except:
    print "W: No log file open"
    pass

def __log(logtype, s):
    s = "[ " + str(datetime.datetime.today()) + "] " + logtype + ": " + s
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
    uid = user + os.sep + repo + "-" + get_timestamp() + "-" + to

    checkout_root = CONFIG['builder_root'] + os.sep + user
    shutil.rmtree(checkout_root + os.sep + repo, True)
    try:
        os.makedirs(checkout_root)
    except OSError:
        pass
    os.chdir(checkout_root)

    git_cmdline_clone       = ["git", "clone", "git://github.com/%s/%s.git" % (user, repo)]
    git_cmdline_checkout    = ["git", "checkout", to]
    git_logging_clone       = open(CONFIG["builder_root"] + os.sep + uid + ".git-clone.log", "w")
    git_logging_checkout    = open(CONFIG["builder_root"] + os.sep + uid + ".git-checkout.log", "w")
    make_logging            = open(CONFIG["builder_root"] + os.sep + uid + ".make.log", "w")

    subprocess.call(git_cmdline_clone, stdout=git_logging_clone, stderr=subprocess.STDOUT)
    os.chdir(repo)

    # We checkout the received git hash to be sure
    subprocess.call(git_cmdline_checkout, stdout=git_logging_checkout, stderr=subprocess.STDOUT)
    subprocess.call("make", stdout=make_logging, stderr=subprocess.STDOUT)

    git_logging_clone.close()
    git_logging_checkout.close()
    make_logging.close()

    build_apk_name = repo + "-debug.apk"

    try:
        os.rename(CONFIG["builder_root"] + os.sep + user + os.sep + repo + os.sep + "bin" + os.sep + build_apk_name,
                  CONFIG["builder_root"] + os.sep + uid + ".apk")
    except:
        info("No apk found")

    info("All data processed")
