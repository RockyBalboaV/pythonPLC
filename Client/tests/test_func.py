import os
import subprocess
import getpass
# from app import get_config

os.environ['env'] = 'dev'
os.environ['url'] = 'server'


# class TestFunction():
#     def test_get_config(self):
#         get_config()

def ntpdate():
    # todo 添加配置读取
    # todo 待测试 使用supervisor启动时用户为root 不需要sudo输入密码 不安全
    pw = 'touhou'
    print(pw)
    password = getpass.getpass()
    print(password)
    ntp_server = 'ntpdate cn.ntp.org.cn'

    cmd2 = 'echo {}fds | sudo -S fdsafs {}'.format(pw, ntp_server)
    ntp = subprocess.Popen(
        cmd2,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print(ntp.wait())  # 判断进程执行状态
    stdout, stderr = ntp.communicate()
    print(stdout.decode('utf-8'), stderr.decode('utf-8'))
    # todo 日志写入


def badblock():
    cmd = 'sudo badblocks -v /dev/mmcblk0p2'
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    print(stdout.decode('utf-8'), stderr.decode('utf-8'))


ntpdate()
