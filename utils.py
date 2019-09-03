import time


def log(*args, **kwargs):
    _format = '%H:%M:%S'
    value = time.localtime(int(time.time()))
    dt = time.strftime(_format, value)
    print(dt, *args, **kwargs)
