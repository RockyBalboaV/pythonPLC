# coding=utf-8
import datetime

from flask_restful import reqparse

# station查询参数
station_parser = reqparse.RequestParser()
station_parser.add_argument('id', type=int, help='该数据的主键')
station_parser.add_argument('station_name', type=str)

station_parser.add_argument('page', type=int)
station_parser.add_argument('per_page', type=int)
station_parser.add_argument('limit', type=int)

station_parser.add_argument('username', type=str)
station_parser.add_argument('password', type=str)
station_parser.add_argument('token', type=str)

# station添加参数
station_put_parser = reqparse.RequestParser()
station_put_parser.add_argument('id', type=int, help='该数据的主键')
station_put_parser.add_argument('station_name', type=str)

station_put_parser.add_argument('username', type=str)
station_put_parser.add_argument('password', type=str)
station_put_parser.add_argument('token', type=str)

station_put_parser.add_argument('station_name', type=str)
station_put_parser.add_argument('mac', type=str)
station_put_parser.add_argument('ip', type=str)
station_put_parser.add_argument('note', type=str)
station_put_parser.add_argument('id_num', type=str)
station_put_parser.add_argument('plc_count', type=int)
station_put_parser.add_argument('ten_id', type=str)
station_put_parser.add_argument('item_id', type=str)
station_put_parser.add_argument('modification', type=bool)

# plc查询参数
plc_parser = reqparse.RequestParser()
plc_parser.add_argument('id', type=int)
plc_parser.add_argument('plc_name', type=str)
plc_parser.add_argument('station_id', type=int, help='plc从属的station')
plc_parser.add_argument('station_name', type=str)

plc_parser.add_argument('page', type=int)
plc_parser.add_argument('per_page', type=int)
plc_parser.add_argument('limit', type=int)

plc_parser.add_argument('username', type=str)
plc_parser.add_argument('password', type=str)
plc_parser.add_argument('token', type=str)

# plc添加参数
plc_put_parser = reqparse.RequestParser()
plc_put_parser.add_argument('id', type=int)
plc_put_parser.add_argument('station_id', type=int, help='plc从属的station')

plc_put_parser.add_argument('username', type=str)
plc_put_parser.add_argument('password', type=str)
plc_put_parser.add_argument('token', type=str)

plc_put_parser.add_argument('plc_name', type=str)
plc_put_parser.add_argument('note', type=str)
plc_put_parser.add_argument('ip', type=str)
plc_put_parser.add_argument('mpi', type=int)
plc_put_parser.add_argument('type', type=int)
plc_put_parser.add_argument('plc_type', type=str)
plc_put_parser.add_argument('ten_id', type=str)
plc_put_parser.add_argument('item_id', type=str)
plc_put_parser.add_argument('rack', type=int)
plc_put_parser.add_argument('slot', type=int)
plc_put_parser.add_argument('tcp_port', type=int)

# group查询参数
group_parser = reqparse.RequestParser()
group_parser.add_argument('id', type=int)
group_parser.add_argument('group_name', type=str)
group_parser.add_argument('plc_id', type=int)
group_parser.add_argument('plc_name', type=str)

group_parser.add_argument('page', type=int)
group_parser.add_argument('per_page', type=int)
group_parser.add_argument('limit', type=int)

group_parser.add_argument('username', type=str)
group_parser.add_argument('password', type=str)
group_parser.add_argument('token', type=str)

# group添加参数
group_put_parser = reqparse.RequestParser()
group_put_parser.add_argument('id', type=int)
group_put_parser.add_argument('plc_id', type=int)

group_put_parser.add_argument('username', type=str)
group_put_parser.add_argument('password', type=str)
group_put_parser.add_argument('token', type=str)

group_put_parser.add_argument('group_name', type=str)
group_put_parser.add_argument('note', type=str)
group_put_parser.add_argument('upload_cycle', type=int)
group_put_parser.add_argument('ten_id', type=str)
group_put_parser.add_argument('item_id', type=str)
group_put_parser.add_argument('upload', type=bool)

# variable查询参数
variable_parser = reqparse.RequestParser()
variable_parser.add_argument('id', type=int)
variable_parser.add_argument('variable_name', type=str)
variable_parser.add_argument('plc_id', type=int)
variable_parser.add_argument('plc_name', type=str)
variable_parser.add_argument('group_id', type=int)
variable_parser.add_argument('group_name', type=str)

variable_parser.add_argument('page', type=int)
variable_parser.add_argument('per_page', type=int)
variable_parser.add_argument('limit', type=int)

variable_parser.add_argument('username', type=str)
variable_parser.add_argument('password', type=str)
variable_parser.add_argument('token', type=str)

# variable添加参数
variable_put_parser = reqparse.RequestParser()
variable_put_parser.add_argument('id', type=int)
variable_put_parser.add_argument('plc_id', type=int)
variable_put_parser.add_argument('group_id', type=int)
variable_put_parser.add_argument('username', type=str)
variable_put_parser.add_argument('password', type=str)
variable_put_parser.add_argument('token', type=str)

variable_put_parser.add_argument('variable_name', type=str)
variable_put_parser.add_argument('db_num', type=int)
variable_put_parser.add_argument('address', type=float)
variable_put_parser.add_argument('data_type', type=str)
variable_put_parser.add_argument('rw_type', type=int)
variable_put_parser.add_argument('upload', type=int)
variable_put_parser.add_argument('acquisition_cycle', type=int)
variable_put_parser.add_argument('server_record_cycle', type=int)
variable_put_parser.add_argument('note', type=str)
variable_put_parser.add_argument('ten_id', type=str)
variable_put_parser.add_argument('item_id', type=str)
variable_put_parser.add_argument('write_value', type=int)
variable_put_parser.add_argument('area', type=float)

# value查询参数
value_parser = reqparse.RequestParser()
value_parser.add_argument('id', type=int)
value_parser.add_argument('plc_id', type=int)
value_parser.add_argument('plc_name', type=str)
value_parser.add_argument('group_id', type=int)
value_parser.add_argument('group_name', type=str)
value_parser.add_argument('variable_id', type=int, action='append')
value_parser.add_argument('variable_name', type=str)
value_parser.add_argument('query_id', type=int)
value_parser.add_argument('query_name', type=str)
value_parser.add_argument('all_variable_id', type=bool)


value_parser.add_argument('min_time', type=int)
value_parser.add_argument('max_time', type=int)

value_parser.add_argument('order_time', type=bool)
value_parser.add_argument('page', type=int)
value_parser.add_argument('per_page', type=int)
value_parser.add_argument('limit', type=int)

value_parser.add_argument('username', type=str)
value_parser.add_argument('password', type=str)
value_parser.add_argument('token', type=str)

# value添加参数
value_put_parser = reqparse.RequestParser()
value_put_parser.add_argument('id', type=int)
value_put_parser.add_argument('variable_id', type=int)
value_put_parser.add_argument('username', type=str)
value_put_parser.add_argument('password', type=str)
value_put_parser.add_argument('token', type=str)

value_put_parser.add_argument('value', type=str)
value_put_parser.add_argument('time', type=int)

# status查询参数
status_parser = reqparse.RequestParser()
status_parser.add_argument('id', type=int)
status_parser.add_argument('station_id', type=int, action='append')

status_parser.add_argument('min_time', type=int)
status_parser.add_argument('max_time', type=int)

status_parser.add_argument('order_time', type=bool)
status_parser.add_argument('page', type=int)
status_parser.add_argument('per_page', type=int)
status_parser.add_argument('limit', type=int)

status_parser.add_argument('username', type=str)
status_parser.add_argument('password', type=str)
status_parser.add_argument('token', type=str)

# status put参数
status_put_parser = reqparse.RequestParser()
status_put_parser.add_argument('id', type=int)
status_put_parser.add_argument('station_id', type=int)
status_put_parser.add_argument('level', type=int)
status_put_parser.add_argument('time', type=int)
status_put_parser.add_argument('note', type=str)
status_put_parser.add_argument('token', type=str)

# 查询变量组查询参数
query_parser = reqparse.RequestParser()
query_parser.add_argument('id', type=int)
query_parser.add_argument('variable_id', type=int, action='append')
query_parser.add_argument('name', type=str)

query_parser.add_argument('min_time', type=int)
query_parser.add_argument('max_time', type=int)
query_parser.add_argument('order_time', type=bool)
query_parser.add_argument('page', type=int)
query_parser.add_argument('per_page', type=int)
query_parser.add_argument('limit', type=int)

# 查询变量组添加参数
query_put_parser = reqparse.RequestParser()
query_put_parser.add_argument('id', type=int)
query_put_parser.add_argument('name', type=str)
query_put_parser.add_argument('variable_id', type=int, action='append')

# 变量警告日志查询

alarm_parser = reqparse.RequestParser()
alarm_parser.add_argument('id', type=int)
alarm_parser.add_argument('status', type=int)

alarm_parser.add_argument('alarm_id', type=int, action='append')
alarm_parser.add_argument('plc_id', type=int, action='append')
alarm_parser.add_argument('variable_id', type=int, action='append')
alarm_parser.add_argument('alarm_type', type=int, action='append')
alarm_parser.add_argument('time', type=int)
alarm_parser.add_argument('all_alarm_id', type=bool)

alarm_parser.add_argument('min_time', type=int)
alarm_parser.add_argument('max_time', type=int)
alarm_parser.add_argument('order_time', type=bool)
alarm_parser.add_argument('page', type=int)
alarm_parser.add_argument('per_page', type=int)
alarm_parser.add_argument('limit', type=int)
alarm_parser.add_argument('token', type=str)

# 添加警告日志

alarm_put_parser = reqparse.RequestParser()
alarm_put_parser.add_argument('id', type=int)
alarm_put_parser.add_argument('status', type=int)
alarm_put_parser.add_argument('alarm_id', type=int)
alarm_put_parser.add_argument('time', type=int)

# 查询当前报警
alarm_now_parser = reqparse.RequestParser()
alarm_now_parser.add_argument('id', type=int)
alarm_now_parser.add_argument('alarm_id', type=int)
alarm_now_parser.add_argument('time', type=int)
alarm_now_parser.add_argument('variable_id', type=int, action='append')

alarm_now_parser.add_argument('page', type=int)
alarm_now_parser.add_argument('per_page', type=int)

# 修改当前报警
alarm_now_put_parser = reqparse.RequestParser()
alarm_now_put_parser.add_argument('id', type=int)
alarm_now_put_parser.add_argument('alarm_id', type=int)
alarm_now_put_parser.add_argument('time', type=int)

# 变量报警信息查询

alarm_info_parser = reqparse.RequestParser()
alarm_info_parser.add_argument('id', type=int)
alarm_info_parser.add_argument('plc_id', type=int, action='append')
alarm_info_parser.add_argument('variable_id', type=int, action='append')
alarm_info_parser.add_argument('alarm_type', type=int)
alarm_info_parser.add_argument('limit', type=int)
alarm_info_parser.add_argument('page', type=int)
alarm_info_parser.add_argument('per_page', type=int)
alarm_info_parser.add_argument('token', type=str)


# 变量报警信息设置

alarm_info_put_parser = reqparse.RequestParser()
alarm_info_put_parser.add_argument('id', type=int)
alarm_info_put_parser.add_argument('variable_id', type=int)

alarm_info_put_parser.add_argument('alarm_type', type=int)
alarm_info_put_parser.add_argument('note', type=str)
alarm_info_put_parser.add_argument('token', type=str)

# 用户认证、用户新建（无认证）
auth_parser = reqparse.RequestParser()
auth_parser.add_argument('username', type=str)
auth_parser.add_argument('password', type=str)
auth_parser.add_argument('email', type=str)
auth_parser.add_argument('expires', type=int)
auth_parser.add_argument('pw_confirm', type=str)
auth_parser.add_argument('role', type=str, action='append')

# 用户查询、用户管理（有认证）
user_parser = reqparse.RequestParser()
user_parser.add_argument('id', type=int)
user_parser.add_argument('username', type=str)
user_parser.add_argument('email', type=str)
user_parser.add_argument('role', type=str, action='append')
user_parser.add_argument('limit', type=int)
user_parser.add_argument('page', type=int)
user_parser.add_argument('per_page', type=int)
user_parser.add_argument('token', type=str)

# 接口日志
interface_parser = reqparse.RequestParser()
interface_parser.add_argument('id', type=int)
interface_parser.add_argument('username', type=str)
interface_parser.add_argument('host_url', type=str)
interface_parser.add_argument('method', type=str)

interface_parser.add_argument('repeal', type=bool)

interface_parser.add_argument('min_time', type=int)
interface_parser.add_argument('max_time', type=int)
interface_parser.add_argument('order_time', type=bool)
interface_parser.add_argument('page', type=int)
interface_parser.add_argument('per_page', type=int)
interface_parser.add_argument('limit', type=int)
interface_parser.add_argument('token', type=str)

# 参数设置
param_parser = reqparse.RequestParser()
param_parser.add_argument('id', type=int)
param_parser.add_argument('variable_id', type=int)
param_parser.add_argument('param_name', type=str)
param_parser.add_argument('unit', type=str)

param_parser.add_argument('page', type=int)
param_parser.add_argument('per_page', type=int)
param_parser.add_argument('limit', type=int)


