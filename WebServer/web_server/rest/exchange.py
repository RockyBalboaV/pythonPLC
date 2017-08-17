import re

f = open('test.py', 'r+')
all_lines = f.readlines()
f.seek(0)
f.truncate()
for line in all_lines:
    print(line)
    new_line = re.sub(r"(\s+if args\[')(.+)('])", r"\1\2\3is not None:", line)
    print(new_line)
    f.write(line)
f.close()
