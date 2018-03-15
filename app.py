import server
import json


def render_form(request, response, id):
    path = './static/form.html'
    with open(path, 'r') as file_obj:
        res_content = file_obj.read()
    server.res_status(response, 302)
    # header = {}
    # server.res_header(request, response, header)
    print(response)
    return res_content


server.add_route("GET", "/form/<id>/user", render_form)


def form_data(request, response):
    print(server.ROUTES)
    content = request["body"]
    content["status"] = "Your name has been submitted"
    res_content = json.dumps(content)
    return res_content


server.add_route("POST", "/api/sendjson", form_data)


def main():
    server.execute_server()


if __name__ == '__main__':
    main()
