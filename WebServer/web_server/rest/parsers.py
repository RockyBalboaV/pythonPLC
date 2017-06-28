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

station_put_parser.add_argument('name', type=str)
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

plc_put_parser.add_argument('name', type=str, required=False, location='json')
plc_put_parser.add_argument('note', type=str)
plc_put_parser.add_argument('ip', type=str)
plc_put_parser.add_argument('mpi', type=int)
plc_put_parser.add_argument('type', type=int)
plc_put_parser.add_argument('plc_type', type=str)
plc_put_parser.add_argument('ten_id', type=str)
plc_put_parser.add_argument('item_id', type=str)


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

variable_put_parser.add_argument('tag_name', type=str)
variable_put_parser.add_argument('address', type=str)
variable_put_parser.add_argument('data_type', type=str)
variable_put_parser.add_argument('rw_type', type=int)    
variable_put_parser.add_argument('upload', type=bool)
variable_put_parser.add_argument('acquisition_cycle', type=int)
variable_put_parser.add_argument('server_record_cycle', type=int)
variable_put_parser.add_argument('note', type=str)
variable_put_parser.add_argument('ten_id', type=str)
variable_put_parser.add_argument('item_id', type=str)


# value查询参数
value_parser = reqparse.RequestParser()
value_parser.add_argument('id', type=int)
value_parser.add_argument('plc_id', type=int)
value_parser.add_argument('plc_name', type=str)
value_parser.add_argument('group_id', type=int)
value_parser.add_argument('group_name', type=str)
value_parser.add_argument('variable_id', type=int)
value_parser.add_argument('variable_name', type=str)

value_parser.add_argument('min_time', type=int)
value_parser.add_argument('max_time', type=int)

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

