import sys
import contextlib


class MISSING(object):
    pass


@contextlib.contextmanager
def traceback_limit(new_limit: int):
    old_limit = getattr(sys, 'tracebacklimit', MISSING)
    sys.tracebacklimit = new_limit
    yield
    if old_limit is MISSING:
        del sys.tracebacklimit
    else:
        sys.tracebacklimit = old_limit
