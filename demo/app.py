#!/usr/bin/env python3
"""Application running to test HTTP server."""

import json
import server


def render_form(request, response, id):
    """Set HTML file to the response content."""
    # return server.redirect(request, response, "https://www.geekskool.com/",
    #                        307)
    path = 'static/form.html'
    with open(path, 'r') as file_obj:
        res_content = file_obj.read()
    server.res_status(response, 302)
    # header = {"Content-Type: "text/html"}
    # server.res_header(response, header)
    return res_content


def form_data(request, response):
    """Send json data to the client."""
    content = request["body"]
    content["status"] = "Done!! \n\nYour name has been submitted"
    res_content = json.dumps(content)
    return res_content


def main():
    """Provide routes for the app."""
    server.add_route("GET", "/form/<id>/user", render_form)
    server.add_route("POST", "/api/sendjson", form_data)
    server.execute_server()


if __name__ == '__main__':
    main()
