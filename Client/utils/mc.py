# coding=u8
from contextlib import contextmanager

from celery.five import monotonic

import pylibmc as memcache

# 初始化memcache连接
mc = memcache.Client(
    ['127.0.0.1'],
    binary=True,
    behaviors={
        'tcp_nodelay': True,
        'ketama': True
    }
)

LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes

@contextmanager
def memcache_lock(lock_id, oid):
    timeout_at = monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = mc.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        # memcache delete is very slow, but we have to use it to take
        # advantage of using add() for atomic locking
        if monotonic() < timeout_at:
            # don't release the lock if we exceeded the timeout
            # to lessen the chance of releasing an expired lock
            # owned by someone else.
            mc.delete(lock_id)
