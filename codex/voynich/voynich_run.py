import json
from tokenizer.tokenizer_v1 import tokenize
from parser.bnf_parser_v1 import parse_token
from interpreter.rel_state_engine_v1 import rel_state

sample = "qokedy qokeedy chedy dain"

tokens = tokenize(sample)
output = []

for t in tokens:
    packet = parse_token(t)
    rs = rel_state(packet)
    output.append({ "token":t, "packet":packet, "rel_state":rs })

with open("state/voynich_out.json","w") as f:
    json.dump(output,f,indent=2)

print(json.dumps(output,indent=2))
