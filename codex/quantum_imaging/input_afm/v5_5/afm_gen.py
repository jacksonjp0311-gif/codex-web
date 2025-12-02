# -*- coding: utf-8 -*-
import numpy as np

def make(shape=(64,64,64)):
    x=np.linspace(-2,2,shape[0])
    y=np.linspace(-2,2,shape[1])
    z=np.linspace(-1,1,shape[2])
    X,Y,Z=np.meshgrid(x,y,z,indexing="ij")
    vol=np.exp(-(X**2+Y**2)*3)*np.exp(-abs(Z)*6)
    vol=(vol-vol.min())/(vol.max()-vol.min())
    return vol.astype(np.float32)

import sys
out=sys.argv[1]
np.save(out,make())
print("[AFM] saved",out)
