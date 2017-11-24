# coding=utf-8
import hmac
import zlib
import base64
import json

from models import Session


def encryption_client(dict_data):
    """
    压缩
    :param dict_data: 
    :return: 
    """

    str_data = json.dumps(dict_data).encode('utf-8')
    zlib_data = zlib.compress(str_data)

    return zlib_data


def decryption_client(base64_data):
    """
    解压
    :param base64_data: 
    :return: 
    """

    zlib_data = base64.b64decode(base64_data)
    str_data = zlib.decompress(zlib_data)
    dict_data = json.loads(str_data)

    return dict_data


def get_data_from_query(models):
    # 输入session.query()查询到的模型实例列表,读取每个实例每个值,放入列表返回
    data_list = []
    for model in models:
        model_column = {}
        for c in model.__table__.columns:
            model_column[c.name] = getattr(model, c.name, None)
        data_list.append(model_column)
    return data_list


def get_data_from_model(model):
    # 读取一个模型实例中的每一项与值，放入字典
    model_column = {}
    for c in model.__table__.columns:
        model_column[c.name] = getattr(model, c.name, None)
    return model_column


def db_write(model):
    session = Session()
    session.add(model)
    session.commit()
