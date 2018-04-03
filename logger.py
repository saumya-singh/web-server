"""Log Information."""

import redis

class Logger:
    """Log info in Redis DB."""

    def __init__(self, DEBUG=False):
        self.DEBUG = DEBUG

    def __call__(self, request, response):
        return self.logger(request, response)

    def logger(self, request, response):
        ip = request["header"]["Host"].split(":")[0]
        method = request["method"]
        path = request["path"]
        date = response["Date"]
        status = response["status"]
        if self.DEBUG:
            log = """Host: {}
            Request Method : {}
            Request Path: {}
            Resonse Details: {} - {}""".format(ip, method, path, date, status)
            print(log)
        redis_obj = redis.StrictRedis(host='localhost', port=6379, db=0)
        redis_obj.hmset(name="{}".format(date), mapping={"ip": ip,
                        "method": method, "path": path, "status": status})
