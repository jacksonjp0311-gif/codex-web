import numpy as np
def compute_delta_phi(L):
    A=np.array(L)
    gx=np.abs(np.diff(A,axis=1)).mean()
    gy=np.abs(np.diff(A,axis=0)).mean()
    return (gx+gy)/2.0
