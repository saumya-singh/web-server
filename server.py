import socket
import pprint
import datetime


CONTENT_TYPE = {
    "html": "text/html",
    "css": "text/css",
    "js": "application/javascript",
    "jpeg": "image/jpeg",
    "ico": "image/x-icon",
    "text": "text/plain",
    "json": "application/json"
}


def form_response(response):
    res = b""
    print(response["status_line"])
    res += response["status_line"] + "\r\n"
    # res += response["Content-Type"] + "\r\n"
    # res += response["Content-Length"] + "\r\n\r\n"
    # res += response["content"]
    # print("====", res.encode() + response["content"])
    return res.encode() + response["content"]


def success_handler(request, response):
    response["status_line"] = "HTTP/1.1 20 OK"
    if response["content"]:
        response["Content-Length"] = str(len(response["content"]))
    response = form_response(response)
    return response


def error_handler(request, response):
    pass


def static_file_handler(request, response):
    try:
        with open("./static" + request["path"], "rb") as file_obj:
            res_body = file_obj.read()
    except OSError:
        return error_handler(request, response)
    response["content"] = res_body
    content_type = request["path"].split(".")[1]
    response["Content-Type"] = CONTENT_TYPE[content_type]
    return success_handler(request, response)


def get_handler(request, response):
    return static_file_handler(request, response)


def method_handler(request, response):
    METHODS = {"GET" : get_handler,
        # "POST" : post_handler,
        # "PUT" : put_handler,
        # "DELETE" : delete_handler
    }
    handler = METHODS[request["method"]]
    return handler(request, response)


def request_handler(request):
    response = {}
    # response = "\nHTTP/1.1 200 OK\n\nHello, World!\n"
    return method_handler(request, response)


def get_query_content(header):
    content = {}
    path, query_params=  header["path"].split("?")
    header["path"] = path
    query_list = query_params.split("&")
    for each_query in query_list:
        key, val = each_query.split("=")
        content[key] = val
    return (header["path"], content)


def header_parser(request, header_stream):
    header = {}
    header_list = header_stream.split(b"\r\n")
    request["method"], request["path"], request["http_version"] = \
                                    (header_list[0].decode()).split(" ")
    if "?" in request["path"]:
        request["path"], request["content"] = get_query_content(header)
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
    return request


def request_parser(request_data):
    request = {}
    header_stream = request_data.split(b"\r\n\r\n")[0]
    request = header_parser(request, header_stream)
    if "Content-Length" in request["header"]:
        body_stream = request_data.split(b"\r\n\r\n")[1]
        request["body"] = body_stream.decode()
    pprint.pprint(request) ##
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
        request = request_parser(request_data)
        http_response = request_handler(request)
        # print("++++++", http_response)
        client_connection.send(http_response)
        client_connection.close()


if __name__ == '__main__':
    execute_server("localhost", 8000)
