#!/usr/bin/env python3
from uuid import uuid4


class Session:

    def __init__(self):
        self.session = {}


    def __call__(self, request, response):
        return self.session_middleware(self, request, response)


    def session_middleware(self, request, response):
        browser_cookies = request["header"].get("Cookie")
        if browser_cookies:
            sid = request["header"]["Cookie"].get("sid")
        if sid:
            return request, response
        sid = str(uuid4())
        response["header"]["Set-Cookie"] = "sid={}".format(sid)
        self.session[sid] = {}
        return request, response


    def add(self, request, content):
            # browser_cookies = request["header"]["Cookies"]
            pass


    def get(self, request):
        try:
            browser_cookies = request["header"].get("Cookie", False)
            sid = request["header"]["Cookie"].get("sid", False)
        except KeyError as key:
            print("No {} in request header\n".format(key))
        if browser_cookies and sid:
            return sid
        return None

    def pop(self, request):
        browser_cookies = request["header"].get("Cookie", False)
        if browser_cookies:
            sid = request["header"]["Cookie"].get("sid", False)
        if sid:
            del SESSIONS[sid]
