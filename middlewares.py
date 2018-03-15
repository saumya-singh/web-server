#!/usr/bin/env python3
'''middleware helper function for server'''

import os
from uuid import uuid4

SESSIONS = {}

def session_middleware(request, response):
    """Add session ids to SESSION """
    browser_cookies = request["header"].get("Cookie", False)
    if browser_cookies:
        sid = request["header"]["Cookie"].get("sid", False)
    if sid:
        return request, response
    cookie = str(uuid4())
    response["header"]["Set-Cookie"] = "sid={}".format(cookie)
    SESSIONS[cookie] = {}
    return request, response


def get_session(request):
    """Get session id from SESSIONS"""
    try:
        browser_cookies = request["header"].get("Cookie", False)
        sid = request["header"]["Cookie"].get("sid", False)
    except KeyError as key:
        print("No {} in request header\n".format(key))
    if browser_cookies and sid:
        return sid
    return None

def del_session(request):
    """Delete session from self.SESSIONS"""
    browser_cookies = request["header"].get("Cookie", False)
    if browser_cookies:
        sid = request["header"]["Cookie"].get("sid", False)
    if sid:
        del SESSIONS[sid]


def logger(request, response):
    client_ip = request["header"]["Host"].split(":")[0]
    log_items = ("Date", "method", "path", "status")
    date, method, path, status = [response[i] for i in log_items]
    log = "{0} - - [{1}] \"{2} {3}\" {4}\n".format(client_ip, date, method, path, status)
    save_logs(log)
    return log, request, response

def save_logs(log, debug=False, filename="http_server.log"):
    if os.path.isfile(filename):
        with open(filename, mode="a") as log_data:
            log_data.write(log)
    if debug:
        print(log, end="")
