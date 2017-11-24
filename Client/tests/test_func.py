import os
import subprocess
import getpass
import requests
import time
import json

import pytest

os.environ['env'] = 'dev'
os.environ['url'] = 'dev-server'

from app import server_confirm, get_config, beats, before_running
from util import encryption_client, decryption_client
from data_collection import analog2digital

# class TestFunction():
#     def test_get_config(self):
#         get_config()
post_data = {
    'count': 103,
    'data': [
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202672,
            'note': '1#\u8bbe\u5907\u5f00\u542f\u8d85\u65f6 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 1,
            'variable_name': 'DT1.StartTimeout'
        },
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202674,
            'note': '1#\u52a0\u70ed\u8d85\u65f6 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 2,
            'variable_name': 'DT1.HeatingTimeout'
        },
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202676,
            'note': '1#\u6e29\u5ea6\u957f\u65f6\u95f4\u4f4e\u4e8e\u8bbe\u5b9a\u503c ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 3,
            'variable_name': 'DT1.LowTemperature'
        },
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202678,
            'note': '2#\u8bbe\u5907\u5f00\u542f\u8d85\u65f6 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 4,
            'variable_name': 'DT2.StartTimeout'
        },
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202680,
            'note': '2#\u52a0\u70ed\u8d85\u65f6 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 5,
            'variable_name': 'DT2.HeatingTimeout'
        },
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202788,
            'note': '2#\u6e29\u5ea6\u957f\u65f6\u95f4\u4f4e\u4e8e\u8bbe\u5b9a\u503c ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 6,
            'variable_name': 'DT2.LowTemperature'
        },
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202790,
            'note': '3#\u8bbe\u5907\u5f00\u542f\u8d85\u65f6 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 7,
            'variable_name': 'DT3.StartTimeout'
        },
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202792,
            'note': '3#\u52a0\u70ed\u8d85\u65f6 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 8,
            'variable_name': 'DT3.HeatingTimeout'
        },
        {
            'group_id': 1,
            'group_name': '\u8b66\u544a',
            'id': 1202794,
            'note': '3#\u6e29\u5ea6\u957f\u65f6\u95f4\u4f4e\u4e8e\u8bbe\u5b9a\u503c ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914814,
            'value': '0',
            'variable_id': 9,
            'variable_name': 'DT3.LowTemperature'
        },
        {
            'group_id': 2,
            'group_name': '\u8b66\u544a',
            'id': 338,
            'note': None,
            'plc_id': 2,
            'plc_name': '\u6d4b\u8bd5\u7528314',
            'time': 1508900310,
            'value': None,
            'variable_id': 10,
            'variable_name': '\u6d4b\u8bd5int 1'
        },
        {
            'group_id': 2,
            'group_name': '\u8b66\u544a',
            'id': 340,
            'note': None,
            'plc_id': 2,
            'plc_name': '\u6d4b\u8bd5\u7528314',
            'time': 1508900310,
            'value': None,
            'variable_id': 11,
            'variable_name': '\u6d4b\u8bd5int 2'
        },
        {
            'group_id': 2,
            'group_name': '\u8b66\u544a',
            'id': 342,
            'note': None,
            'plc_id': 2,
            'plc_name': '\u6d4b\u8bd5\u7528314',
            'time': 1508900310,
            'value': None,
            'variable_id': 12,
            'variable_name': '\u6d4b\u8bd5float 1'
        },
        {
            'group_id': 2,
            'group_name': '\u8b66\u544a',
            'id': 344,
            'note': None,
            'plc_id': 2,
            'plc_name': '\u6d4b\u8bd5\u7528314',
            'time': 1508900310,
            'value': None,
            'variable_id': 13,
            'variable_name': '\u6d4b\u8bd5float 2'
        },
        {
            'group_id': 2,
            'group_name': '\u8b66\u544a',
            'id': 346,
            'note': None,
            'plc_id': 2,
            'plc_name': '\u6d4b\u8bd5\u7528314',
            'time': 1508900310,
            'value': None,
            'variable_id': 14,
            'variable_name': '\u6d4b\u8bd5bool 1'
        },
        {
            'group_id': 2,
            'group_name': '\u8b66\u544a',
            'id': 348,
            'note': None,
            'plc_id': 2,
            'plc_name': '\u6d4b\u8bd5\u7528314',
            'time': 1508900310,
            'value': None,
            'variable_id': 15,
            'variable_name': '\u6d4b\u8bd5bool 2'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202795,
            'note': '1#\u7f50\u6db2\u4f4d',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0.869502305984497',
            'variable_id': 16,
            'variable_name': 'DT1LT01'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202796,
            'note': '2#\u7f50\u6db2\u4f4d',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '1.44473373889923',
            'variable_id': 17,
            'variable_name': 'DT2LT01'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202797,
            'note': '\u96c6\u6c34\u6c60\u6db2\u4f4d',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0.675491869449615',
            'variable_id': 18,
            'variable_name': 'DT3LT01'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202798,
            'note': '3#\u7f50\u6db2\u4f4d',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '1.22554981708527',
            'variable_id': 19,
            'variable_name': 'DT4LT11'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202799,
            'note': '1#\u7f50\u9876\u538b\u529b',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '-0.0350837707519531',
            'variable_id': 20,
            'variable_name': 'DT1PT01'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202800,
            'note': '1#\u7f50\u6e29\u5ea6',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '-5',
            'variable_id': 21,
            'variable_name': 'DT2PT01'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202801,
            'note': '2#\u7f50\u9876\u538b\u529b',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '-0.00258969515562057',
            'variable_id': 22,
            'variable_name': 'DT3PT01'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202802,
            'note': '2#\u7f50\u6e29\u5ea6',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '67.96875',
            'variable_id': 23,
            'variable_name': 'DT1TT01'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202803,
            'note': '3#\u7f50\u9876\u538b\u529b',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '58.2754592895508',
            'variable_id': 24,
            'variable_name': 'DT2TT01'
        },
        {
            'group_id': 3,
            'group_name': '\u6a21\u62df\u91cf',
            'id': 1202804,
            'note': '3#\u7f50\u6e29\u5ea6',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '71.6145858764648',
            'variable_id': 25,
            'variable_name': 'DT3TT01'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202699,
            'note': '1#\u7f50\u8fd0\u884c\u6807\u8bb0',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 26,
            'variable_name': 'DT1.Strt'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202700,
            'note': '1#\u7f50\u6682\u505c\u6807\u8bb0',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 27,
            'variable_name': 'DT1.Pause'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202701,
            'note': '1#\u7f50\u5de5\u827a\u6b65\u53f7',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 28,
            'variable_name': 'DT1.StepNo'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202702,
            'note': '1#\u7f50\u5de5\u827a\u8fd0\u884c\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 29,
            'variable_name': 'DT1.RrTm'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202703,
            'note': '1#\u7f50\u5de5\u827a\u6b65\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 30,
            'variable_name': 'DT1.SrTm'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202704,
            'note': '2#\u7f50\u8fd0\u884c\u6807\u8bb0',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 31,
            'variable_name': 'DT2.Strt'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202705,
            'note': '2#\u7f50\u6682\u505c\u6807\u8bb0',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 32,
            'variable_name': 'DT2.Pause'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202706,
            'note': '2#\u7f50\u5de5\u827a\u6b65\u53f7',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 33,
            'variable_name': 'DT2.StepNo'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202707,
            'note': '2#\u7f50\u5de5\u827a\u8fd0\u884c\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 34,
            'variable_name': 'DT2.RrTm'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202708,
            'note': '2#\u7f50\u5de5\u827a\u6b65\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 35,
            'variable_name': 'DT2.SrTm'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202709,
            'note': '3#\u7f50\u8fd0\u884c\u6807\u8bb0',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 36,
            'variable_name': 'DT3.Strt'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202710,
            'note': '3#\u7f50\u6682\u505c\u6807\u8bb0',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 37,
            'variable_name': 'DT3.Pause'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202711,
            'note': '3#\u7f50\u5de5\u827a\u6b65\u53f7',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 38,
            'variable_name': 'DT3.StepNo'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202712,
            'note': '3#\u7f50\u5de5\u827a\u8fd0\u884c\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 39,
            'variable_name': 'DT3.RrTm'
        },
        {
            'group_id': 4,
            'group_name': '\u5355\u5143\u4fe1\u606f',
            'id': 1202713,
            'note': '3#\u7f50\u5de5\u827a\u6b65\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 40,
            'variable_name': 'DT3.SrTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202820,
            'note': '1#\u7f50\u542f\u52a8\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '10',
            'variable_id': 63,
            'variable_name': 'DT1.StpTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202821,
            'note': '1#\u7f50\u8fdb\u6599\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '540',
            'variable_id': 64,
            'variable_name': 'DT1.Filling_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202822,
            'note': '1#\u7f50\u51fa\u6599\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '780',
            'variable_id': 65,
            'variable_name': 'DT1.Out_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202823,
            'note': '1#\u7f50\u52a0\u70ed\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '5400',
            'variable_id': 66,
            'variable_name': 'DT1.Heat_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202824,
            'note': '1#\u7f50\u7ed3\u675f\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '5',
            'variable_id': 67,
            'variable_name': 'DT1.EndTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202825,
            'note': '1#\u7f50\u542f\u52a8\u6b65\u7f50\u6db2\u4f4d\u4f4e\u503c\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '2.5',
            'variable_id': 68,
            'variable_name': 'DT1.Level_LowSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202826,
            'note': '1#\u7f50\u8fdb\u6599\u8bbe\u5b9a\u6db2\u4f4d\u9ad8\u503c ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '2.79999995231628',
            'variable_id': 69,
            'variable_name': 'DT1.Filling_LevelSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202827,
            'note': '1#\u7f50\u51fa\u6599\u8bbe\u5b9a\u6db2\u4f4d\u4f4e\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 70,
            'variable_name': 'DT1.Out_LevelSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202828,
            'note': '1#\u7f50\u7f50\u4f53\u538b\u529b\u9ad8\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0.200000002980232',
            'variable_id': 71,
            'variable_name': 'DT1.P_HighSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202829,
            'note': '1#\u7f50\u7f50\u4f53\u538b\u529b\u4f4e\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '-0.200000002980232',
            'variable_id': 72,
            'variable_name': 'DT1.P_LowSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202830,
            'note': '1#\u7f50\u52a0\u70ed\u6b65\u6e29\u5ea6\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '90.8000030517578',
            'variable_id': 73,
            'variable_name': 'DT1.T_HeatSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202831,
            'note': '1#\u7f50\u4fdd\u6e29\u6b65\u6e29\u5ea6\u4f4e\u503c\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '90',
            'variable_id': 74,
            'variable_name': 'DT1.T_TucSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202832,
            'note': '2#\u7f50\u542f\u52a8\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '10',
            'variable_id': 75,
            'variable_name': 'DT2.StpTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202833,
            'note': '2#\u7f50\u8fdb\u6599\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '540',
            'variable_id': 76,
            'variable_name': 'DT2.Filling_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202834,
            'note': '2#\u7f50\u51fa\u6599\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '780',
            'variable_id': 77,
            'variable_name': 'DT2.Out_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202835,
            'note': '2#\u7f50\u52a0\u70ed\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '5400',
            'variable_id': 78,
            'variable_name': 'DT2.Heat_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202836,
            'note': '2#\u7f50\u7ef4\u6301\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '600',
            'variable_id': 79,
            'variable_name': 'DT2.TucTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202837,
            'note': '2#\u7f50\u7ed3\u675f\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '5',
            'variable_id': 80,
            'variable_name': 'DT2.EndTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202838,
            'note': '2#\u7f50\u542f\u52a8\u6b65\u7f50\u6db2\u4f4d\u4f4e\u503c\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '2.5',
            'variable_id': 81,
            'variable_name': 'DT2.Level_LowSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202839,
            'note': '2#\u7f50\u8fdb\u6599\u8bbe\u5b9a\u6db2\u4f4d\u9ad8\u503c ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '4',
            'variable_id': 82,
            'variable_name': 'DT2.Filling_LevelSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202840,
            'note': '2#\u7f50\u51fa\u6599\u8bbe\u5b9a\u6db2\u4f4d\u4f4e\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 83,
            'variable_name': 'DT2.Out_LevelSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202841,
            'note': '2#\u7f50\u7f50\u4f53\u538b\u529b\u9ad8\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '5.09999990463257',
            'variable_id': 84,
            'variable_name': 'DT2.P_HighSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202842,
            'note': '2#\u7f50\u7f50\u4f53\u538b\u529b\u4f4e\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '-5.09999990463257',
            'variable_id': 85,
            'variable_name': 'DT2.P_LowSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202843,
            'note': '2#\u7f50\u52a0\u70ed\u6b65\u6e29\u5ea6\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '91',
            'variable_id': 86,
            'variable_name': 'DT2.T_HeatSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202844,
            'note': '2#\u7f50\u4fdd\u6e29\u6b65\u6e29\u5ea6\u4f4e\u503c\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '90',
            'variable_id': 87,
            'variable_name': 'DT2.T_TucSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202845,
            'note': '2#\u7f50\u52a0\u70ed\u6b65\u6db2\u4f4d\u4f4e\u62a5\u8b66',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '1',
            'variable_id': 88,
            'variable_name': 'DT2.Level_LowAlarm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202846,
            'note': '3#\u7f50\u542f\u52a8\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '10',
            'variable_id': 89,
            'variable_name': 'DT3.StpTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202847,
            'note': '3#\u7f50\u8fdb\u6599\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '540',
            'variable_id': 90,
            'variable_name': 'DT3.Filling_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202848,
            'note': '3#\u7f50\u51fa\u6599\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '780',
            'variable_id': 91,
            'variable_name': 'DT3.Out_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202849,
            'note': '3#\u7f50\u52a0\u70ed\u6b65\u6700\u957f\u5de5\u827a\u65f6\u95f4',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '5400',
            'variable_id': 92,
            'variable_name': 'DT3.Heat_MorTm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202744,
            'note': '3#\u7f50\u7ef4\u6301\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '600',
            'variable_id': 93,
            'variable_name': 'DT3.TucTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202745,
            'note': '3#\u7f50\u7ed3\u675f\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '5',
            'variable_id': 94,
            'variable_name': 'DT3.EndTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202746,
            'note': '3#\u7f50\u542f\u52a8\u6b65\u7f50\u6db2\u4f4d\u4f4e\u503c\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '4.01999998092651',
            'variable_id': 95,
            'variable_name': 'DT3.Level_LowSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202747,
            'note': '3#\u7f50\u8fdb\u6599\u8bbe\u5b9a\u6db2\u4f4d\u9ad8\u503c ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '2.70000004768372',
            'variable_id': 96,
            'variable_name': 'DT3.Filling_LevelSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202748,
            'note': '3#\u7f50\u51fa\u6599\u8bbe\u5b9a\u6db2\u4f4d\u4f4e\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0.600000023841858',
            'variable_id': 97,
            'variable_name': 'DT3.Out_LevelSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202749,
            'note': '3#\u7f50\u7f50\u4f53\u538b\u529b\u9ad8\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0.100000001490116',
            'variable_id': 98,
            'variable_name': 'DT3.P_HighSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202750,
            'note': '3#\u7f50\u7f50\u4f53\u538b\u529b\u4f4e\u503c',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '-0.100000001490116',
            'variable_id': 99,
            'variable_name': 'DT3.P_LowSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202751,
            'note': '3#\u7f50\u52a0\u70ed\u6b65\u6e29\u5ea6\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '90.8000030517578',
            'variable_id': 100,
            'variable_name': 'DT3.T_HeatSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202752,
            'note': '3#\u7f50\u4fdd\u6e29\u6b65\u6e29\u5ea6\u4f4e\u503c\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '90',
            'variable_id': 101,
            'variable_name': 'DT3.T_TucSet'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202753,
            'note': '3#\u7f50\u52a0\u70ed\u6b65\u6db2\u4f4d\u4f4e\u62a5\u8b66',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '1.51999998092651',
            'variable_id': 102,
            'variable_name': 'DT3.Level_LowAlarm'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202754,
            'note': '1#\u7f50\u7ef4\u6301\u6b65\u65f6\u95f4\u8bbe\u5b9a',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '600',
            'variable_id': 103,
            'variable_name': 'DT1.TucTime'
        },
        {
            'group_id': 5,
            'group_name': '\u53c2\u6570',
            'id': 1202755,
            'note': '1#\u7f50\u52a0\u70ed\u6b65\u6db2\u4f4d\u4f4e\u62a5\u8b66',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '1.5',
            'variable_id': 104,
            'variable_name': 'DT1.Level_LowAlarm'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202756,
            'note': '1#\u7f50\u6709\u8bbe\u5907\u5904\u4e8e\u624b\u52a8\u72b6\u6001 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 41,
            'variable_name': 'DT1.ManMode'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202757,
            'note': '1#\u7f50\u6db2\u4f4d\u9ad8 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 42,
            'variable_name': 'DT1.HighLevel'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202758,
            'note': '1#\u7f50\u7f50\u4f53\u538b\u529b\u8d85\u9ad8 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 43,
            'variable_name': 'DT1.HighPressure'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202759,
            'note': '1#\u7f50\u7f50\u4f53\u538b\u529b\u8d85\u4f4e ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 44,
            'variable_name': 'DT1.LowPressure'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202760,
            'note': '1#\u7f50\u51fa\u6599\u9600\u672a\u5173\u95ed',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 45,
            'variable_name': 'DT1.OutValveOpen'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202761,
            'note': '1#\u7f50\u6db2\u4f4d\u8fc7\u4f4e ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 46,
            'variable_name': 'DT1.LowLevel'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202762,
            'note': '1#\u7f50\u8fdb\u6599\u9600\u672a\u5173\u95ed ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 47,
            'variable_name': 'DT1.FillingValveOpen'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202763,
            'note': '2#\u7f50\u6709\u8bbe\u5907\u5904\u4e8e\u624b\u52a8\u72b6\u6001 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 48,
            'variable_name': 'DT2.ManMode'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202764,
            'note': '2#\u7f50\u6db2\u4f4d\u9ad8 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 49,
            'variable_name': 'DT2.HighLevel'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202765,
            'note': '2#\u7f50\u7f50\u4f53\u538b\u529b\u8d85\u9ad8 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 50,
            'variable_name': 'DT2.HighPressure'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202766,
            'note': '2#\u7f50\u7f50\u4f53\u538b\u529b\u8d85\u4f4e ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 51,
            'variable_name': 'DT2.LowPressure'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202767,
            'note': '2#\u7f50\u51fa\u6599\u9600\u672a\u5173\u95ed ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 52,
            'variable_name': 'DT2.OutValveOpen'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202768,
            'note': '2#\u7f50\u6db2\u4f4d\u8fc7\u4f4e ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 53,
            'variable_name': 'DT2.LowLevel'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202769,
            'note': '2#\u7f50\u8fdb\u6599\u9600\u672a\u5173\u95ed ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 54,
            'variable_name': 'DT2.FillingValveOpen'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202770,
            'note': '3#\u7f50\u6709\u8bbe\u5907\u5904\u4e8e\u624b\u52a8\u72b6\u6001 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 55,
            'variable_name': 'DT3.ManMode'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202771,
            'note': '3#\u7f50\u6db2\u4f4d\u9ad8 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 56,
            'variable_name': 'DT3.HighLevel'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202772,
            'note': '3#\u7f50\u7f50\u4f53\u538b\u529b\u8d85\u9ad8 ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 57,
            'variable_name': 'DT3.HighPressure'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202773,
            'note': '3#\u7f50\u7f50\u4f53\u538b\u529b\u8d85\u4f4e ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 59,
            'variable_name': 'DT3.LowPressure'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202774,
            'note': '3#\u7f50\u51fa\u6599\u9600\u672a\u5173\u95ed ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 60,
            'variable_name': 'DT3.OutValveOpen'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202775,
            'note': '3#\u7f50\u8fdb\u6599\u9600\u672a\u5173\u95ed ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 61,
            'variable_name': 'DT3.FillingValveOpen'
        },
        {
            'group_id': 6,
            'group_name': '\u62a5\u8b66',
            'id': 1202776,
            'note': '3#\u7f50\u6db2\u4f4d\u8fc7\u4f4e ',
            'plc_id': 1,
            'plc_name': '\u6c61\u6c34\u7ad91',
            'time': 1509914776,
            'value': '0',
            'variable_id': 62,
            'variable_name': 'DT3.LowLevel'
        }
    ],
    'msg': '\u67e5\u8be2\u6210\u529f',
    'page': 1,
    'pages': None,
    'per_page': 10,
    'status': 0,
    'total': None
}


class TestFunc(object):
    @pytest.mark.skip
    def ntpdate(self):
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

    @pytest.mark.skip
    def badblock(self):
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

    # @pytest.mark.skip
    def test_encryption_decryption(self):
        time1 = time.time()
        data = encryption_client(post_data)
        time2 = time.time()
        print(time2 - time1)

        rp = requests.post('http://127.0.0.1:11000/client/test', data=data)
        assert rp.status_code == 200

        print(len(rp.content))

        time1 = time.time()
        data = decryption_client(rp.content)
        time2 = time.time()
        print(time2 - time1)
        print(len(json.dumps(data)))
        assert data == post_data

    def test_analog2digital(self):
        analog_low_range = 0
        analog_high_range = 30000
        digital_low_range = 0
        digital_high_range = 100

        raw_value = 15000
        value = analog2digital(raw_value, analog_low_range, analog_high_range, digital_low_range, digital_high_range)

        assert int(value) == 50

        raw_value = 10000
        value = analog2digital(raw_value, analog_low_range, analog_high_range, digital_low_range, digital_high_range)

        assert round(value, 1) == 33.3


class TestTask(object):
    def test_get_config(self):
        get_config()

get_config()
# beats()
# ntpdate()
# before_running()