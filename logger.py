"""Log Information."""

import redis

class Logger:
    """Log info in Redis Graph DB."""

    def __init__(self, DEBUG=False, FILENAME=""):
        self.DEBUG = DEBUG
        self.FILENAME = FILENAME

    def __call__(self, request, response):
        return self.logger(request, response)

    def logger(self, request, response):
        ip = request["header"]["Host"].split(":")[0]
        date = response["Date"]
        method = request["method"]
        path = request["path"]
        status = response["status"]
        log = "{} - - [{}] \"{} {}\" {}\n".format(date, method,
                                                  path, status)
        self.write_print_logs(log)
        return request, response

    def write_logs(self, log):
        # if self.DEBUG:
        #     print(log, end="")
        # with open(self.FILENAME, mode="a") as log_data:
        #     log_data.write(log)
        r = redis.StrictRedis()
        reply = r.execute_command('GRAPH.QUERY', 'logs', "CREATE ()")
