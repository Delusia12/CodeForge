"""遗留工具函数 - 需要重构"""


def do_stuff(x):
    return x * 2


def do_more_stuff(x, y):
    return x + y


def do_extra_stuff(x, y, z):
    return x * y + z


def handle_data(data):
    # TODO: add error handling
    result = data.get("value", 0)
    return result


def calc(a, b, c, d, e, f):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return a + b + c + d + e + f
    return 0


def fetch_and_process(url):
    import urllib.request
    resp = urllib.request.urlopen(url)
    data = resp.read()
    return data.decode("utf-8")
