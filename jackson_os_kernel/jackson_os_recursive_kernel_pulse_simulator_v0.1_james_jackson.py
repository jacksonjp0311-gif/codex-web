# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Recursive Kernel Pulse Simulator v0.1  
Authored by James Jackson  
Origin Law: Law CII â€” Systemic Recursion  
Lineage: Jackson OS, September 2025  
This module animates full-system recursion seeded by authored laws and feedback loops.
"""
from codex.utils.safe_eval import safe_eval

import numpy as np 
import matplotlib .pyplot as plt 
import matplotlib .animation as animation 

# Kernel Pulse Cycle
class KernelPulseSimulator :
    def __init__ (self ,laws ,signal_seed ):
        self .laws =laws 
        self .signal_seed =signal_seed 
        self .cycles =self ._generate_cycles ()

    def _generate_cycles (self ):
        cycles =[]
        base =self .signal_seed 
        for law in self .laws :
            mutated =base *safe_eval (law .replace ("amplitude","1.0"))
            cycles .append (mutated )
            base =mutated +np .random .normal (0 ,0.02 ,len (base ))
        return cycles 

    def animate (self ):
        fig ,ax =plt .subplots ()
        line ,=ax .plot ([],[],lw =2 )
        ax .set_xlim (0 ,len (self .signal_seed ))
        ax .set_ylim (0.3 ,1.8 )
        ax .set_title ("Recursive Kernel Pulse â€” Jackson OS")

        def update (frame ):
            line .set_data (range (len (self .cycles [frame ])),self .cycles [frame ])
            ax .set_ylabel (f"Cycle {frame +1 }")
            return line ,

        ani =animation .FuncAnimation (fig ,update ,frames =len (self .cycles ),interval =500 ,blit =True )
        plt .tight_layout ()
        plt .show ()

        # Example laws and signal
laws =["amplitude * 1.1","amplitude * 0.95","amplitude * 1.2","amplitude * 0.88"]
signal_seed =np .random .normal (0.6 ,0.1 ,100 )

simulator =KernelPulseSimulator (laws ,signal_seed )
simulator .animate ()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_recursive_kernel_pulse_simulator_v0.1_james_jackson')
