#!/usr/bin/env python3
'''simple local HTTP server'''

import mimetypes
import asyncio
import pprint
import json
import re
import os


METHODS = ("GET", "POST", "OPTIONS")
ROUTES = {method: {} for method in METHODS}

def build_regex_path(path):
    pattern_obj = re.compile(r'(<\w+>)')
    regex = pattern_obj.sub(r'(?P\1.+)', path)
    return '^{}$'.format(regex)

def add_route(method, path, function):
    regex_path = build_regex_path(path)
    ROUTES[method][regex_path] = function

def make_response(response):
    res = response["status_line"] + "\r\n"
    for key, value in response.items():
        if key not in ["status_line", "content"]:
            res += "{0}: {1}\r\n".format(key, value)
    res += "\r\n"
    res_bytes = res.encode()
    if "content" in response:
        res_bytes += response["content"]
    return res_bytes

def ok_200_add_headers(response):
    response["status_line"] = "HTTP/1.1 200 OK"
    if response["content"]:
        response["Content-Length"] = str(len(response["content"]))
    return make_response(response)

def err_404_handler(request, response, next_):
    response["status_line"] = "HTTP/1.1 404 Not Found"
    return make_response(response)

def route_handler(request, response, next_):
    flag = 0
    if request["method"] == "GET":
        routes = ROUTES["GET"]
    elif request["method"] == "POST":
        routes = ROUTES["POST"]
    for regex, function in routes.items():
        answer = re.match(regex, request["path"])
        if answer:
            res_body = function(request, response, **answer.groupdict())
            flag = 1
            break
    if flag == 0:
        return next_(request, response, next_)
    response["content"] = res_body.encode()
    return ok_200_add_headers(response)

def static_file_handler(request, response, next_):
    print("\n\n{}\n\n".format("!"*33))
    if request["method"] == "GET":
        if request["path"][-1] == "/":
            request["path"] += "index.html"
        filename = "static{}".format(request["path"])
        if not os.path.isfile(filename):
            return next_(request, response, next_)
        response["Content-Type"] = mimetypes.guess_type(request["path"])[0]
        with open(filename, "rb") as file_obj:
            res_body = file_obj.read()
        response["content"] = res_body
        return ok_200_add_headers(response)
    return next_(request, response, next_)

def body_handler(request, response, next_):
    content_type = request["header"].get("Content-Type", False)
    if content_type:
        request["body"] = json.loads(request["body"])
    return next_(request, response, next_)

def create_next():
    counter = 0
    def next_func(request, response, next_):
        nonlocal counter
        func = HANDLERS[counter]
        counter += 1
        return func(request, response, next_)
    return next_func

def request_handler(request):
    if "query_content" in request:
        no = request["query_content"]["n"]
        l = int(no)^500
        j = 0
        print("{0} stuck in loop {0}".format("*"*16))
        for i in range(l):
            j = j + i
    response = {}
    # response = "\nHTTP/1.1 200 OK\n\nHello, World!\n"
    next_ = create_next()
    return next_(request, response, next_)

def get_query_content(request):
    path, query_params = request["path"].split("?")
    query_content = dict([query.split("=") for query in query_params.split("&")])
    return (path, query_content)

def header_parser(header_stream):
    req_line, *header_list = header_stream.split("\r\n")
    request = dict(zip(["method", "path", "http_version"], req_line.split()))

    if "?" in request["path"]:
        request["path"], request["query_content"] = get_query_content(request)

    header = dict([hdr.split(": ") for hdr in header_list])
    if "Cookie" in header:
        header["Cookie"] = dict([cookie.split("=") for cookie in header["Cookie"].split(";")])
    request["header"] = header
    return request

def body_parser(body_stream, content_type):
    # application/x-www-form-urlencoded , multipart/form-data, application/json
    if content_type == "application/json":
        parsed_body = json.loads(body_stream)
    elif content_type == "application/x-www-form-urlencoded":
        parsed_body = query_parser(body_stream)
    elif content_type == "multipart/form-data":
        pass
    return parsed_body


def query_parser(query_string):
    query_str = query_string.split("&")
    query_dict = dict([query.split("=") for query in query_str])
    return query_dict

async def handle_message(reader, writer):
    # addr = writer.get_extra_info('peername')
    # print("Received from %r" % (addr))
    print("entered handle_message")
    header = await reader.readuntil(b'\r\n\r\n')
    header_stream = header.decode().split("\r\n\r\n")[0]
    print("\n{0}\n\n{1}\n\n{0}\n".format("="*50, header_stream))
    request = header_parser(header_stream)
    content_length = request["header"].get("Content-Length", False)
    content_type = request["header"].get("Content-Type", False)
    if content_length or content_type:
        body_stream = await reader.readexactly(int(content_length))
        print("{0} {1} {0}".format("+"*15, body_stream.decode()))
        request["body"] = body_stream.decode()
        # request["body"] = body_parser(body_stream.decode(), content_type)
    pprint.pprint(request)
    response = request_handler(request)
    writer.write(response)
    await writer.drain()
    print("Close the client socket")
    writer.close()


def execute_server(host='127.0.0.1', port=8000):
    print("entered execute_server")
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_message, host, port, loop=loop)
    server = loop.run_until_complete(coro)
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever() # ???
    except KeyboardInterrupt:
        print("\nShutting down the server...\n")
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


HANDLERS = [body_handler, static_file_handler, route_handler, err_404_handler]

if __name__ == '__main__':
    execute_server()
