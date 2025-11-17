import matplotlib.pyplot as plt
import numpy as np
def save_lattice_heatmap(L,path):
    plt.figure(figsize=(6,6))
    plt.imshow(np.array(L),cmap='viridis')
    plt.colorbar()
    plt.title('DNA Lattice Heatmap')
    plt.savefig(path,dpi=200)
    plt.close()
