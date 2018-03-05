import socket
import pprint
import json


CONTENT_TYPE = {
    "html": "text/html",
    "css": "text/css",
    "js": "application/javascript",
    "jpeg": "image/jpeg",
    "ico": "image/x-icon",
    "text": "text/plain",
    "json": "application/json",
    "png": "image/png",
    "gif": "image/gif",
    "xml": "application/xml",
    "pdf": "application/pdf"
    }


ROUTES = {
    "GET" : {},
    "POST" : {}
    }


def add_route(method, path, function):
    ROUTES[method][path] = function


def make_response(response):
    res = ""
    res_bytes = b""
    res += response["status_line"] + "\r\n"
    for key, value in response.items():
        if key not in ["status_line", "content"]:
            res += "{0}: {1}\r\n".format(key, value)
    res += "\r\n"
    res_bytes += res.encode()
    if "content" in response:
        res_bytes += response["content"]
    response = res_bytes
    return response


def ok_200_add_headers(response):
    response["status_line"] = "HTTP/1.1 200 OK"
    if response["content"]:
        response["Content-Length"] = str(len(response["content"]))
    response = make_response(response)
    return response


def err_404_handler(request, response, next_):
    response["status_line"] = "HTTP/1.1 404 Not Found"
    response = make_response(response)
    return response


def route_handler(request, response, next_):
    if request["method"] == "GET":
        routes = ROUTES["GET"]
    elif request["method"] == "POST":
        routes = ROUTES["POST"]
    try:
        if request["path"][-1] == "/":
            request["path"] += "index.html"
        function = routes[request["path"]]
        res_body = function(request, response)
        response["content"] = res_body.encode()
        return ok_200_add_headers(response)
    except KeyError:
        return next_(request, response, next_)


def static_file_handler(request, response, next_):
    if request["method"] == "GET":
        try:
            if request["path"][-1] == "/":
                request["path"] += "index.html"
            with open("./static" + request["path"], "rb") as file_obj:
                res_body = file_obj.read()
        except OSError:
            return next_(request, response, next_)
        content_type = request["path"].split(".")[1]
        response["Content-Type"] = CONTENT_TYPE[content_type]
        response["content"] = res_body
        return ok_200_add_headers(response)
    else:
        return next_(request, response, next_)


def body_handler(request, response, next_):
    if "Content-Type" in request["header"] and "application/json" \
                                        in request["header"]["Content-Type"]:
        request["body"] = json.loads(request["body"])
    return next_(request, response, next_)


handler_list = [body_handler, static_file_handler, route_handler,\
                                                    err_404_handler]
                                                    
def create_next():
    counter = 0
    def next_func(request, response, next_):
        nonlocal counter
        func = handler_list[counter]
        counter += 1
        return func(request, response, next_)
    return next_func


def request_handler(request):
    response = {}
    # response = "\nHTTP/1.1 200 OK\n\nHello, World!\n"
    next_ = create_next()
    return next_(request, response, next_)


def get_query_content(request):
    content = {}
    path, query_params = request["path"].split("?")
    request["path"] = path
    query_list = query_params.split("&")
    for each_query in query_list:
        key, val = each_query.split("=")
        content[key] = val
    return (request["path"], content)


def header_parser(request, header_stream):
    header = {}
    header_list = header_stream.split(b"\r\n")
    request["method"], request["path"], request["http_version"] = \
                                    (header_list[0].decode()).split(" ")
    if "?" in request["path"]:
        request["path"], request["content"] = get_query_content(request)
    header_list.pop(0)
    for one_header in header_list:
        key, value = (one_header.decode()).split(": ")
        header[key] = value
    if "Cookie" in header:
        cookie_content = {}
        cookies = header["Cookie"].split(";")
        for each_cookie in cookies:
            key, val = each_cookie.split("=")
            cookie_content[key] = val
        header["Cookie"] = cookie_content
    request["header"] = header


def request_parser(request_data):
    request = {}
    header_stream = request_data.split(b"\r\n\r\n")[0]
    header_parser(request, header_stream)
    if "Content-Length" in request["header"]:
        body_stream = request_data.split(b"\r\n\r\n")[1]
        request["body"] = body_stream.decode()
    return request


def execute_server(HOST, PORT):
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((HOST, PORT))
    listen_socket.listen(1)
    print('Serving HTTP on port %s ...' % PORT)
    while True:
        client_connection, client_address = listen_socket.accept()
        request_data = client_connection.recv(1024)
        if request_data == b'':
            client_connection.close()
        print("*********")
        print(request_data)
        print("*********")
        request = request_parser(request_data)
        print("==================")
        pprint.pprint(request)
        print("==================")
        http_response = request_handler(request)
        print("response:\n", http_response)
        client_connection.send(http_response)
        client_connection.close()


if __name__ == '__main__':
    execute_server("localhost", 8000)
