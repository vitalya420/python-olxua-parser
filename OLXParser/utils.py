from queue import Queue


def read_proxy_from_file(filename, protocol, encoding="utf-8") -> Queue:
    proxy_queue = Queue()
    with open(filename, "r", encoding=encoding) as file:
        proxies = file.read().split("\n")
        for proxy in proxies:
            if ":" not in proxy:
                continue
            ip, port = proxy.split(":")
            proxy_queue.put({"http": f"{protocol}://{ip}:{port}",
                             "https": f"{protocol}://{ip}:{port}"})
    return proxy_queue
