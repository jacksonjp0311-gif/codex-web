import math
def build_lattice(e,width=64):
    h = math.ceil(len(e)/width)
    L=[]
    for i in range(h):
        row=e[i*width:(i+1)*width]
        row += [0.0]*(width-len(row))
        L.append(row)
    return L
