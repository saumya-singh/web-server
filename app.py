#!/usr/bin/env python3
'''test application running to test HTTP server'''

import json
import server

def render_form(request, response, id):
<<<<<<< HEAD
    print("$$$$$$$$$$$$", id)
    path = 'static/form.html'
=======
    path = './static/form.html'
>>>>>>> 70f71bb482444c3537726f08716a09b2f9fc5862
    with open(path, 'r') as file_obj:
        res_content = file_obj.read()
    server.res_status(response, 302)
    # header = {}
    # server.res_header(request, response, header)
    print(response)
    return res_content

def form_data(request, response):
    print(server.ROUTES)
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
