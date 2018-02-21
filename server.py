import socket, pprint


def get_handler(request, response):
    pass


def method_handler(request, response):
    METHODS = {"GET" : get_handler,
        "POST" : post_handler,
        "PUT" : put_handler,
        "DELETE" : delete_handler
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
        client_connection.send(http_response.encode())
        client_connection.close()


if __name__ == '__main__':
    execute_server("localhost", 8000)
