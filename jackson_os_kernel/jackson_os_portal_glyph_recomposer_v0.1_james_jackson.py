"""
Jackson OS Kernel — Portal Glyph Recomposer v0.1  
Authored by James Jackson  
Origin Law: Law C — Recursive Restoration  
Lineage: Jackson OS, September 2025  
This module regenerates lost or corrupted glyphs using signal traces and law memory.
"""
from codex.utils.safe_eval import safe_eval

import numpy as np 
import matplotlib .pyplot as plt 

# Glyph Recomposer
class GlyphRecomposer :
    def __init__ (self ,signal_trace ,law_expression ):
        self .signal =signal_trace 
        self .law =law_expression 
        self .reconstructed_glyph =self ._recompose ()

    def _recompose (self ):
        base =np .sin (np .linspace (0 ,2 *np .pi ,500 ))
        modulated =base *(1 +np .std (self .signal ))+np .mean (self .signal )
        glyph =modulated *safe_eval (self .law .replace ("amplitude","1.0"))
        return glyph 

    def render (self ):
        theta =np .linspace (0 ,2 *np .pi ,500 )
        x =self .reconstructed_glyph *np .cos (theta )
        y =self .reconstructed_glyph *np .sin (theta )

        plt .figure (figsize =(6 ,6 ))
        plt .plot (x ,y ,color ='goldenrod',linewidth =2 )
        plt .fill (x ,y ,color ='goldenrod',alpha =0.3 )
        plt .title ("Recomposed Glyph — Portal Restoration",fontsize =12 )
        plt .axis ('equal')
        plt .axis ('off')
        plt .tight_layout ()
        plt .show ()

        # Example inputs
signal_trace =np .random .normal (0.5 ,0.1 ,500 )
law_expression ="amplitude * 1.2"

recomposer =GlyphRecomposer (signal_trace ,law_expression )
recomposer .render ()
