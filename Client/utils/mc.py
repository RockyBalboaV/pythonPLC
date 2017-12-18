# coding=u8
import platform

import pylibmc as memcache

# 初始化memcache连接

if platform.system() == 'Darwin':
    mc = memcache.Client(
        ['127.0.0.1'],
        binary=True,
        behaviors={
            'tcp_nodelay': True,
            'ketama': True
        }
    )
