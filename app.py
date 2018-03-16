#!/usr/bin/env python3
'''application running to test HTTP server'''

import json
import server


def render_form(request, response, id):
    # return server.redirect(request, response, "http://www.example.com/", 307)
    path = 'static/form.html'
    with open(path, 'r') as file_obj:
        res_content = file_obj.read()
    # server.res_status(response, 302)
    # header = {}
    # server.res_header(request, response, header)
    return res_content


def form_data(request, response):
    content = request["body"]
    content["status"] = "Done!! \n\nYour name has been submitted"
    res_content = json.dumps(content)
    return res_content


def main():
    server.add_route("GET", "/form/<id>/user", render_form)
    server.add_route("POST", "/api/sendjson", form_data)
    server.execute_server()


if __name__ == '__main__':
    main()
