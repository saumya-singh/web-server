#!/usr/bin/env python3
"""Server to serve web applications."""

from email.utils import formatdate
from http import HTTPStatus
import mimetypes
import asyncio
import pprint
import json
import re
import os


METHODS = ("GET", "POST", "PUT", "DELETE", "OPTIONS")
ROUTES = {method: {} for method in METHODS}


def res_header(response, header):
    """Add header provided by application to response header."""
    response["header"].update(header)


def res_status(response, status):
    """Add status provided by application to response header."""
    status_dict = HTTPStatus.__dict__['_value2member_map_']
    status = status_dict.get(status, False)
    if status:
        response_phrase = status.name.replace("_", " ").title()
        response["status"] = "{0} {1}".format(status.value, response_phrase)
    else:
        raise ValueError("Invalid status code")


def build_regex_path(path):
    """Bulid path regex for routes."""
    pattern_obj = re.compile(r'(<\w+>)')
    regex = pattern_obj.sub(r'(?P\1.+)', path)
    return '^{}$'.format(regex)


def add_route(method, path, function):
    """Add routes regex amd function to ROUTES dictionary."""
    regex_path = build_regex_path(path)
    ROUTES[method][regex_path] = function


def redirect(request, response, path, code):
    """Redirect the response to Location."""
    res_status(response, code)
    response["header"]["Location"] = path
    res = response_handler(request, response)
    return res


def make_response(response):
    """Convert response dictionary to response byte-stream."""
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
    """Add headers to response."""
    response["header"]["Date"] = formatdate(usegmt=True)
    response["header"]["Connection"] = "close"
    # response["server"] = ""
    if "content" not in response:
        response["header"]["Content-Length"] = str(0)
    res = make_response(response)
    return res


def ok_200_handler(request, response):
    """Add status line and content length if success."""
    if "status" not in response:
        response["status"] = "200 OK"
    if "content" in response:
        response["header"]["Content-Length"] = str(len(response["content"]))
    response = response_handler(request, response)
    return response


def err_404_handler(request, response, next_):
    """Add status line if fails."""
    if "status" not in response:
        response["status"] = "404 Not Found"
    response = response_handler(request, response)
    return response


def route_handler(request, response, next_):
    """Handle the routes and execute the desired function."""
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
    if isinstance(res_body, bytes):  # for redirect
        return res_body
    if res_body is not None:
        response["content"] = res_body.encode()
    return ok_200_handler(request, response)


def static_file_handler(request, response, next_):
    """Give the contents of the static files."""
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
    """Parse the body of request."""
    content_type = request["header"].get("Content-Type", False)
    if content_type:
        request["body"] = json.loads(request["body"].decode())
        # print(f'\n\n\n\n{request["body"]}\n\n\n')
    return next_(request, response, next_)


def create_next():
    """Go to the next function in HANDLERS list."""
    counter = 0

    def next_func(request, response, next_):
        nonlocal counter
        func = HANDLERS[counter]
        counter += 1
        return func(request, response, next_)
    return next_func


def request_handler(request):
    """Handels request to give the response."""
    response = {"protocol_version": "HTTP/1.1", "header": {}}
    # response = "\nHTTP/1.1 200 OK\n\nHello, World!\n"
    next_ = create_next()
    return next_(request, response, next_)


def get_query_content(request):
    """Parse the query content into a dictionary."""
    path, query_params = request["path"].split("?")
    query_content = dict([query.split("=") for query in query_params.split
                         ("&")])
    return (path, query_content)


def header_parser(header_stream):
    """Parse the request headers."""
    req_line, *header_list = header_stream.split("\r\n")
    request = dict(zip(["method", "path", "http_version"], req_line.split()))

    if "?" in request["path"]:
        request["path"], request["query_content"] = get_query_content(request)

    header = dict([hdr.split(": ") for hdr in header_list])
    if "Cookie" in header:
        header["Cookie"] = dict([cookie.split("=") for cookie in
                                header["Cookie"].split(";")])
    request["header"] = header
    return request


def body_parser(request):
    """Parse the request body."""
    content_type = request["header"]["Content-Type"]
    body_stream = request["body"]
    # application/x-www-form-urlencoded , multipart/form-data, application/json
    if content_type == "application/json":
        request["body"] = json.loads(body_stream.decode())
    elif content_type == "application/x-www-form-urlencoded":
        request["body"] = query_parser(body_stream.decode())
    elif "multipart/form-data" in content_type:
        request = form_parser(request)
    return request


def hdr2dict(subhdr):
    """Parse multipart form header into a dictionary."""
    subhdr = [i.strip() for i in subhdr.splitlines()]
    subhdr_dict = {}
    for item in subhdr:
        if ":" in item:
            item_dict = dict([item.split(":")])
        elif ";" in item:
            item_dict = dict([i.split("=") for i in item.split(";")])
        elif "=" in item and ";" not in item:
            item_dict = dict([item.split("=")])
        else:
            continue
        subhdr_dict.update(item_dict)
    if subhdr_dict:
        return subhdr_dict


def form_parser(request):
    """Parse the multipart/form-data."""
    content_type = request["header"]["Content-Type"]
    boundary_value = content_type.split(";")[-1].split("=")[-1]
    boundary = "--{}".format(boundary_value).encode()
    multiform_data = request["body"].split(boundary)[1:-1]
    sub_hdrs = [form[0].decode().split("form-data; ")[-1]
                for form in multiform_data]
    sub_body = [form[1].strip() for form in multiform_data]
    form_dict = {}
    for index, subhdr in enumerate(sub_hdrs):
        name = hdr2dict(subhdr)["name"]
        subhdr_dict = dict([("header", hdr2dict(subhdr)),
                           (name, sub_body[index])])
        form_dict.update(subhdr_dict)
    request["form"] = form_dict
    return request


def query_parser(query_string):
    """Parse the urlencoded request body."""
    query_str = query_string.split("&")
    query_dict = dict([query.split("=") for query in query_str])
    return query_dict


async def handle_message(reader, writer):
    """Parse the request."""
    # addr = writer.get_extra_info('peername')
    header = await reader.readuntil(b'\r\n\r\n')
    print("===header===", header)
    header_stream = header.decode().split("\r\n\r\n")[0]
    request = header_parser(header_stream)
    if "Content-Length" in request["header"]:
        con_len = request["header"]["Content-Length"]
        request["body"] = await reader.readexactly(int(con_len))
        # request["body"] = body_parser(body_stream.decode(), content_type)
    pprint.pprint(request)
    response = request_handler(request)
    print("="*30, "\n", response, "\n", "="*30)
    writer.write(response)
    await writer.drain()
    print("Close the client socket")
    writer.close()


def execute_server(host='0.0.0.0', port=8000):  # def execute_server(host='127.0.0.1', port=8000):
    """Execute the server."""
    loop = asyncio.get_event_loop()
    # loop.set_debug()
    coro = asyncio.start_server(handle_message, host, port, loop=loop)
    server = loop.run_until_complete(coro)
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...\n")
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


HANDLERS = [body_handler, static_file_handler, route_handler, err_404_handler]
# HANDLERS = [body_handler, session_handler, static_file_handler, route_handler, err_404_handler]


if __name__ == '__main__':
    execute_server()
