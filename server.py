#!/usr/bin/en python3

from email.utils import formatdate
import mimetypes
import asyncio
import pprint
import json
import re
import os
from http import HTTPStatus
# import logging


METHODS = ("GET", "POST", "OPTIONS")
ROUTES = {method: {} for method in METHODS}


def make_status_phrase(phrase):
    words = phrase.split("_")
    status_phrase = ""
    for word in words:
        status_phrase += word[0] + word[1:].lower() + " "
    return status_phrase.strip()


def res_header(response, header):
    response["header"].update(header)


def res_status(response, status):
    status_dict = HTTPStatus.__dict__['_value2member_map_']
    status = status_dict.get(status, False)
    if status:
        status_phrase = make_status_phrase(status.name)
        response["status"] = "{} {}".format(status.value, status_phrase)
    else:
        raise ValueError

def build_regex_path(path):
    pattern_obj = re.compile(r'(<\w+>)')
    regex = pattern_obj.sub(r'(?P\1.+)', path)
    return '^{}$'.format(regex)

def add_route(method, path, function):
    regex_path = build_regex_path(path)
    ROUTES[method][regex_path] = function

def redirect(request, response, path):
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    response["status"] = "302 Found"
    response["Location"] = path
    res = response_handler(request, response)
    return res

def make_response(response):
    res = response["protocol_version"] + " " + response["status"] + "\r\n"
    if response["header"]:
        for key, value in response["header"].items():
            res += "{0}: {1}\r\n".format(key, value)
    res += "\r\n"
    res_bytes = res.encode()
    if "content" in response:
        res_bytes += response["content"]
    return res_bytes

def response_handler(request, response):
    req_header = request["header"]
    # res_header = response["header"]
    response["header"]["Date"] = formatdate(usegmt=True)
    response["header"]["Connection"] = "close"
    # response["server"] = ""
    res = make_response(response)
    return res

def ok_200_handler(request, response):
    if "status" not in response:
        response["status"] = "200 OK"
    if response["content"]:
        response["header"]["Content-Length"] = str(len(response["content"]))
    response = response_handler(request, response)
    return response

def err_404_handler(request, response, next_):
    if "status" not in response:
        response["status"] = "404 Not Found"
    response = response_handler(request, response)
    return response

def route_handler(request, response, next_):
    flag = 0
    routes = ROUTES[request["method"]]
    for regex, function in routes.items():
        answer = re.match(regex, request["path"])
        if answer:
            res_body = function(request, response, **answer.groupdict())
            flag = 1
            break
    if flag == 0:
        return next_(request, response, next_)
    response["content"] = res_body.encode()
    return ok_200_handler(request, response)

def static_file_handler(request, response, next_):
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
        return ok_200_handler(request, response)
    return next_(request, response, next_)

def body_handler(request, response, next_):
    content_type = request["header"].get("Content-Type", False)
    if content_type:
        request["body"] = json.loads(request["body"])
        # print(f'\n\n\n\n{request["body"]}\n\n\n')
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
    response = {"protocol_version" : "HTTP/1.1", "header": {}}
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

def body_parser(request):
    content_type = request["header"]["Content-Type"]
    body_stream = request["body"]
    # application/x-www-form-urlencoded , multipart/form-data, application/json
    if content_type == "application/json":
        request["body"] = json.loads(body_stream)
    elif content_type == "application/x-www-form-urlencoded":
        request["body"] = query_parser(body_stream)
    elif "multipart/form-data" in content_type:
        request = form_parser(request)
    return request

def form_parser(request):
    content_type = request["header"]["Content-Type"]
    body_stream = request["body"]

    boundary_value = content_type.split(";")[-1].split("=")[-1]
    boundary = "--{}".format(boundary_value).encode()
    multiform_data = [i.split(b"\r\n\r\n", 1) for i in body_stream.split(boundary)]
    sub_hdrs = [form[0].split(b"\r\n") for form in multiform_data]
    hdr_params = [hdr.split(b":")[-1] for hdr in sub_hdrs if b":" in hdr]
    form_dict = {}
    for index, subhdr_param in enumerate(hdr_params):
        params = [param.split(b";") for param in subhdr_param]
        subform = dict([param.split("=") for param in params if b"=" in param])
        subform[b"body"] = multiform_data[index][1]
        form_dict[subform[b"name"]] = subform
    request["form"] = form_dict
    return request


def query_parser(query_string):
    query_str = query_string.split("&")
    query_dict = dict([query.split("=") for query in query_str])
    return query_dict

async def handle_message(reader, writer):
    # addr = writer.get_extra_info('peername')
    header = await reader.readuntil(b'\r\n\r\n')
    header_stream = header.decode().split("\r\n\r\n")[0]
    request = header_parser(header_stream)
    if "Content-Length" in request["header"]:
        con_len = request["header"]["Content-Length"]
        body_stream = await reader.readexactly(int(con_len))
        request["body"] = body_stream.decode()
        # request["body"] = body_parser(body_stream.decode(), content_type)
    pprint.pprint(request)
    response = request_handler(request)
    print("===========================")
    print(response)
    writer.write(response)
    await writer.drain()
    print("Close the client socket")
    writer.close()


def execute_server(host='0.0.0.0', port=8000):
# def execute_server(host='127.0.0.1', port=8000):
    print("entered execute_server")
    loop = asyncio.get_event_loop()
    # loop.set_debug()
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
