class Cache:
    def get(self, name):
        return None

    def put(self, name, ip, ttl):
        pass


def query_upstream(name, cfg):
    return ("SERVER_ERROR", None, None)
