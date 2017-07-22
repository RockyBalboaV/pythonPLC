# coding=utf-8
from libmc import (
    Client, MC_HASH_MD5, MC_POLL_TIMEOUT, MC_CONNECT_TIMEOUT, MC_RETRY_TIMEOUT
)

mc = Client(
    [
        'localhost',
        'localhost:11212',
        'localhost:11213 mc_213'
    ],
    # 分割小于10M的的值
    do_split=True,
    # 所有类型的值编码为字符串
    comp_threshold=0,
    # 更新缓存操作不需要服务端响应，提高操作速度
    noreply=False,
    # 缓存键前缀
    prefix=None,
    # 哈希函数标示
    hash_fn=MC_HASH_MD5,
    # 服务器不可用时，是否做故障转移
    failover=False
)

mc.config(MC_POLL_TIMEOUT, 100)
mc.config(MC_CONNECT_TIMEOUT, 300)
mc.config(MC_RETRY_TIMEOUT, 5)
