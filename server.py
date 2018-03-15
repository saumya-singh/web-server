from email.utils import formatdate
import mimetypes
import requests
import asyncio
import pprint
import json
import re


CONTENT_TYPE =  mimetypes.types_map


ROUTES = {
    "GET" : {},
    "POST" : {}
    }


def make_status_phrase(phrase):
    words = phrase.split("_")
    status_phrase = ""
    for word in words:
        status_phrase += word[0].upper() + word[1:] + " "
    return status_phrase.strip()


def res_header(response, header):
    response["header"].update(header)


def res_status(response, status):
    try:
        phrase = requests.status_codes._codes[status]
        status_phrase = make_status_phrase(phrase[0])
    except KeyError:
        print("Not a VALID STATUS")
        raise ValueError("not a valid status code")
    response["status"] = str(status) + " " + status_phrase


def build_regex_path(path):
    pattern_obj = re.compile(r'(<\w+>)')
    regex = pattern_obj.sub(r'(?P\1.+)', path)
    return '^{}$'.format(regex)


def add_route(method, path, function):
    regex_path = build_regex_path(path)
    ROUTES[method][regex_path] = function


def redirect(path):
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
    response = res_bytes
    return response


def response_handler(request, response):
    request["header"] = req_header
    response["header"] = res_header
    res_header["Date"] = formatdate(timeval=None, localtime=False, usegmt=True)
    res_header["Connection"] = "close"
    # response["server"] = ""
    if response["content"]:
        if "Accept-Encoding" in req_header:
            res_header["Content-Encoding"] = req_header["Accept-Encoding"]
        if "Accept-Language" in  req_header:
            res_header["Content-Language"] = req_header["Accept-Language"]
        if "Accept" in req_header:
            res_header["Content-Type"] = req_header["Accept"]
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
    return ok_200_handler(request, response)


def static_file_handler(request, response, next_):
    if request["method"] == "GET":
        try:
            if request["path"][-1] == "/":
                request["path"] += "index.html"
            with open("./static" + request["path"], "rb") as file_obj:
                res_body = file_obj.read()
        except OSError:
            return next_(request, response, next_)
        content_type = "." + request["path"].split(".")[1]
        response["header"].update({"Content-Type": CONTENT_TYPE[content_type]})
        response["content"] = res_body
        return ok_200_handler(request, response)
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
    response = {"protocol_version" : "HTTP/1.1", "header": {}}
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
    header_list = header_stream.split("\r\n")
    request["method"], request["path"], request["http_version"] = \
                                    (header_list[0]).split(" ")
    if "?" in request["path"]:
        request["path"], request["query_content"] = get_query_content(request)
    header_list.pop(0)
    for one_header in header_list:
        key, value = one_header.split(": ")
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


async def handle_message(reader, writer):
    # addr = writer.get_extra_info('peername')
    header = await reader.readuntil(b'\r\n\r\n')
    header_stream = header.decode().split("\r\n\r\n")[0]
    request = {}
    request = header_parser(request, header_stream)
    if "Content-Length" in request["header"]:
        con_len = request["header"]["Content-Length"]
        body_stream = await reader.readexactly(int(con_len))
        request["body"] = body_stream.decode()
    pprint.pprint(request)
    response = request_handler(request)
    print("===========================")
    print(response)
    writer.write(response)
    await writer.drain()
    print("Close the client socket")
    writer.close()


def execute_server():
    print("entered execute_server")
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_message, '127.0.0.1', 8000, loop=loop)
    server = loop.run_until_complete(coro)
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    execute_server()
