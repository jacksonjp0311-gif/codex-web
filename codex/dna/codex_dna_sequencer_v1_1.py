from engine_energy.dna_nucleotide_map import map_sequence_to_energy
from engine_energy.dna_lattice_builder import build_lattice
from engine_information.dna_delta_phi import compute_delta_phi
from engine_consciousness.dna_visualizer import save_lattice_heatmap
import json,os
from datetime import datetime

def run(seq,out='state/v1_1/'):
    e=map_sequence_to_energy(seq)
    L=build_lattice(e)
    dp=float(compute_delta_phi(L))

    ts=datetime.now().strftime('%Y%m%d_%H%M%S')
    png=f'visuals/lattice/dna_lattice_{ts}.png'
    save_lattice_heatmap(L,png)

    os.makedirs(out,exist_ok=True)
    jp=f'{out}/dna_run_{ts}.json'
    with open(jp,'w') as f:
        json.dump({'seq_length':len(seq),
                   'delta_phi':dp,
                   'timestamp':ts,
                   'visual_path':png},f,indent=4)
    return dp
