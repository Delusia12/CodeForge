"""测试用的坏代码样本"""


def overly_nested_function(data):
    result = None
    if data is not None:
        if "items" in data:
            items = data["items"]
            if len(items) > 0:
                total = 0
                for item in items:
                    if item.get("active", False):
                        if item.get("price", 0) > 0:
                            total += item["price"]
                result = total
    return result


def long_function_with_issues():
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    j = 10
    k = 11
    l = 12
    m = 13
    n = 14
    o = 15
    p = 16
    q = 17
    r = 18
    s = 19
    t = 20
    u = 21
    v = 22
    w = 23
    x = 24
    y = 25
    z = 26
    aa = 27
    bb = 28
    cc = 29
    dd = 30
    ee = 31
    ff = 32
    gg = 33
    hh = 34
    ii = 35
    jj = 36
    kk = 37
    ll = 38
    mm = 39
    nn = 40
    oo = 41
    pp = 42
    qq = 43
    rr = 44
    ss = 45
    tt = 46
    uu = 47
    vv = 48
    ww = 49
    xx = 50
    yy = 51
    zz = 52
    return a + b + c + d + e


def dangerous_query(user_input):
    sql = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return sql


def bare_except_demo():
    try:
        risky_operation()
    except:
        pass


def risky_operation():
    return 1 / 0
