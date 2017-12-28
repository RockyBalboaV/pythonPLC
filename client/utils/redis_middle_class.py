# -*- coding:utf-8 -*-
import redis
import pickle
from contextlib import contextmanager

from celery.five import monotonic


class ConnDB(object):
    def __init__(self):
        # 创建对本机数据库的连接对象
        pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
        self.conn = redis.StrictRedis(connection_pool=pool)

    # 存储
    def set(self, key_, value_):
        # 将数据pickle.dumps一下，转化为二进制bytes数据
        value_ = pickle.dumps(value_)
        # 将数据存储到数据库
        self.conn.set(key_, value_)

    # 读取
    def get(self, key_):
        # 从数据库根据键（key）获取值
        value_ = self.conn.get(key_)
        if value_ is not None:
            value_ = pickle.loads(value_)  # 加载bytes数据，还原为python对象
            return value_
        else:
            return []  # 为None(值不存在)，返回空列表

    # 添加
    def append(self, key_, value_):
        value_ = pickle.dumps(value_)
        self.conn.append(key_, value_)

    def get_all(self, key_):
        self.conn.hegtall('')


pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
redis_conn = redis.StrictRedis(connection_pool=pool)
LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


@contextmanager
def redis_lock(lock_id, oid):
    # 模仿celery文档中提供的memcached进程锁，改用redis，速度慢上好几倍
    timeout_at = monotonic() + LOCK_EXPIRE - 3
    status = redis_conn.set(lock_id, oid, ex=LOCK_EXPIRE, nx=True)
    try:
        yield status
    finally:
        if monotonic() < timeout_at:
            redis_conn.delete(lock_id)


r = ConnDB()
