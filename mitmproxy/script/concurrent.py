"""
This module provides a @concurrent decorator primitive to
offload computations from mitmproxy's main master thread.
"""

from mitmproxy import eventsequence
from mitmproxy.coretypes import basethread


class ScriptThread(basethread.BaseThread):
    name = "ScriptThread"


def concurrent(fn):
    if fn.__name__ not in eventsequence.Events - {"load", "configure", "tick"}:
        raise NotImplementedError(
            "Concurrent decorator not supported for '%s' method." % fn.__name__
        )

    def _concurrent(obj):
        def run():
            fn(obj)
            if obj.reply.state == "taken":
                if not obj.reply.has_message:
                    obj.reply.ack()
                obj.reply.commit()
        obj.reply.take()
        ScriptThread(
            "script.concurrent (%s)" % fn.__name__,
            target=run
        ).start()
    # Support @concurrent for class-based addons
    if "." in fn.__qualname__:
        return staticmethod(_concurrent)
    else:
        return _concurrent
