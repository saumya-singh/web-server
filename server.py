import asyncio
import pprint
import json, re


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


def res_headers(response, headers):
    response["headers"] = headers


def res_status(response, status):
    response["status"] = status


def build_regex_path(path):
    pattern_obj = re.compile(r'(<\w+>)')
    regex = pattern_obj.sub(r'(?P\1.+)', path)
    return '^{}$'.format(regex)


def add_route(method, path, function):
    regex_path = build_regex_path(path)
    ROUTES[method][regex_path] = function


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
    response["header"] = "HTTP/1.1"
    if "status" not in response:
        response["status"] = "200 OK"
    if response["content"]:
        response["Content-Length"] = str(len(response["content"]))
    response = make_response(response)
    return response


def err_404_handler(request, response, next_):
    response["header"] = "HTTP/1.1"
    if "status" not in response:
        response["status"] = "404 Not Found"
    response = make_response(response)
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
    return ok_200_add_headers(response)


def static_file_handler(request, response, next_):
    print("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n")
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
    # if "query_content" in request:
    #     no = request["query_content"]["n"]
    #     l = int(no)^500
    #     j = 0
    #     print("****************stuck in loop, ****************")
    #     for i in range(l):
    #         j = j + i
    #     print("------calculation done------------")
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
    addr = writer.get_extra_info('peername')
    print("entered handle_message")
    header = await reader.readuntil(b'\r\n\r\n')
    header_stream = header.decode().split("\r\n\r\n")[0]
    print("==========", header_stream, "===========")
    request = {}
    request = header_parser(request, header_stream)
    if "Content-Length" in request["header"]:
        con_len = request["header"]["Content-Length"]
        body_stream = await reader.readexactly(int(con_len))
        print("++++++++++", body_stream.decode(), "++++++++++++")
        request["body"] = body_stream.decode()
    pprint.pprint(request)
    response = request_handler(request)
    print("got response")
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
