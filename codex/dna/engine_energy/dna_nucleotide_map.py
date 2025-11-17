NUCLEOTIDE_MAP = {"A":1.0,"T":-1.0,"C":0.5,"G":-0.5}
def map_sequence_to_energy(seq): return [NUCLEOTIDE_MAP.get(b,0.0) for b in seq]
