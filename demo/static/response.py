import pprint


response = {}


def response():
    header = {}
    def status(status):
        response["status"] = status
        pprint.pprint(response)
    return status


res = response()
res.status(200)
