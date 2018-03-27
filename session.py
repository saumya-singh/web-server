#!/usr/bin/env python3
from uuid import uuid4


class Session:
    """Session middleware for web server."""

    def __init__(self):
        """Initialize session dictionary."""
        self.SESSION = {}

    def __call__(self, request, response):
        """Return updated response object."""
        return self.session_middleware(request, response)

    def session_middleware(self, request, response):
        """Add sessions to the self.session."""
        browser_cookies = request["header"].get("Cookie")
        if browser_cookies:
            sid = request["header"]["Cookie"].get("sid")
        if sid:
            return request, response
        sid = str(uuid4())
        response["header"]["Set-Cookie"] = "sid={}".format(sid)
        self.SESSION[sid] = {}
        return request, response

    def add(self, request, content):
        """Add content to sid dictionary."""
        browser_cookies = request["header"].get("Cookie")
        if browser_cookies:
            sid = request["header"]["Cookie"].get("sid")
        if sid:
            self.SESSION[sid].update(content)

    def get(self, request, key):
        """Get session data from self.SESSION."""
        try:
            browser_cookies = request["header"].get("Cookie", False)
            sid = request["header"]["Cookie"].get("sid", False)
        except KeyError:
            print("Session ID missing in request header\n")
        if browser_cookies and sid:
            if key in self.SESSION[sid]:
                return self.SESSION[sid][key]
            else:
                print("{} not provided for the session.".format(key))
        return None

    def pop(self, request):
        """Delete sid from self.session."""
        browser_cookies = request["header"].get("Cookie")
        if browser_cookies:
            sid = request["header"]["Cookie"].get("sid")
        if sid:
            del self.session[sid]
