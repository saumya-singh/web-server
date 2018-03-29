"""Log Information."""

import redis

class Logger:
    """Log info in Redis DB."""

    def __init__(self, DEBUG=False, FILENAME=""):
        self.FILENAME = FILENAME

    def __call__(self, request, response):
        return self.logger(request, response)

    def logger(self, request, response):
        date = response["Date"]
        method = request["method"]
        path = request["path"]
        status = response["status"]
        log = "{} - {} - {} - {}".format(date, method, path, status)
        self.write_print_logs(log)
        return request, response

    def write_logs(self, log):
        r = redis.StrictRedis()
        reply = r.execute_command()
