import re
def tokenize(line):
    tokens = re.findall(r"[a-z]+", line)
    return tokens
