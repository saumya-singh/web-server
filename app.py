import server
import json


def render_form(request, response, id):
    print("$$$$$$$$$$$$", id)
    path = './static/form.html'
    with open(path, 'r') as file_obj:
        content = file_obj.read()
    return content


server.add_route("GET", "/form/<id>/user", render_form)


def form_data(request, response):
    print(server.ROUTES)
    print("???????", request)
    content = request["body"]
    content["status"] = "Your name has been submitted"
    res_content = json.dumps(content)
    return res_content


server.add_route("POST", "/api/sendjson", form_data)


def main():
    server.execute_server()


if __name__ == '__main__':
    main()
