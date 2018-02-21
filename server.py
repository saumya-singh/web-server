import socket, pprint


# METHODS = {"GET" : get_handler,
#     "POST" : post_handler,
#     "PUT" : put_handler,
#     "DELETE" : delete_handler
# }


def header_parser(header_stream):
    header = {}
    header_list = header_stream.split(b"\r\n")
    method, path, http_version = (header_list[0].decode()).split(" ")
    header["method"] = method
    header["path"] = path
    header["http_version"] = http_version
    no_of_headers = len(header_list)
    for index in range(1, no_of_headers):
        one_header = header_list[index].decode()
        colon_pos = one_header.find(":")
        header_name = one_header[ : colon_pos]
        header[header_name] = one_header[colon_pos + 2 : ]
    return header


def request_parser(request_data):
    header_stream = request_data.split(b"\r\n\r\n")[0]
    header = header_parser(header_stream)
    # pprint.pprint(header)
    if "Content-Length" in header:
        body_stream = request_data.split(b"\r\n\r\n")[1]
        # print(body_stream)
    response = "\nHTTP/1.1 200 OK\n\nHello, World!\n"
    return response


def execute_server(HOST, PORT):
    # HOST, PORT = '', 8000
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((HOST, PORT))
    listen_socket.listen(1)
    print('Serving HTTP on port %s ...' % PORT)
    while True:
        client_connection, client_address = listen_socket.accept()
        request_data = client_connection.recv(1024)
        print(request_data)
        http_response = request_parser(request_data)
        client_connection.send(http_response.encode())
        client_connection.close()


if __name__ == '__main__':
    execute_server("localhost", 8000)
