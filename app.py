#!/usr/bin/env python3
'''test application running to test HTTP server'''

import json
import server

def render_form(request, response, id):
    print("$$$$$$$$$$$$", id)
    path = 'static/form.html'
    with open(path, 'r') as file_obj:
        content = file_obj.read()
    return content

def form_data(request, response):
    print(server.ROUTES)
    print("???????", request)
    content = request["body"]
    content["status"] = "Done!! \nYour name has been submitted"
    res_content = json.dumps(content)
    return res_content

def main():
    server.add_route("GET", "/form/<id>/user", render_form)
    server.add_route("POST", "/api/sendjson", form_data)
    server.execute_server()

if __name__ == '__main__':
    main()
