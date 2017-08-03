import re

f = open('api_variable.py', 'r+')
all_lines = f.readlines()
f.seek(0)
f.truncate()