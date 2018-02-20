import socket


def execute_server(HOST, PORT):
    # HOST, PORT = '', 8000
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((HOST, PORT))
    listen_socket.listen(1)
    print('Serving HTTP on port %s ...' % PORT)
    while True:
        client_connection, client_address = listen_socket.accept()
        request = client_connection.recv(1024)
        http_response = "\nHTTP/1.1 200 OK\n\nHello, World!\n"
        client_connection.send(http_response.encode())
        client_connection.close()


if __name__ == '__main__':
    execute_server("localhost", 8000)
