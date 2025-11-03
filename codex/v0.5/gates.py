# =========================================================
# Codex Gate Audit System — v0.2
# Author: James Paul Jackson
# Purpose: Evaluate triadic symmetry and signal alignment for Codex OS
# =========================================================

import math, random

class BaseGate:
    def __init__(self, name, threshold=0.5, weight=1.0, critical=False):
        self.name = name
        self.threshold = threshold
        self.weight = weight
        self.critical = critical

    def evaluate(self, payload):
        '''To be overridden by each gate subclass.'''
        raise NotImplementedError


# --- PHI GATE ---
class PhiGate(BaseGate):
    '''Tests geometric harmony using phi (1.618...) ratio deviations.'''
    def evaluate(self, payload):
        phi = payload.get('phi_estimate', 1.618)
        diff = abs(phi - 1.6180339887)
        score = max(0, 1 - diff)  # higher = more aligned
        return min(1.0, score)


# --- FREQUENCY GATE ---
class FreqGate(BaseGate):
    '''Tests resonance alignment using Schumann / 432 Hz harmonics.'''
    def evaluate(self, payload):
        freq = payload.get('freq_peak', 7.83)
        # convert to relative Schumann band (~7.83 Hz fundamental)
        diff = abs(freq - 7.83) / 7.83
        score = max(0, 1 - diff)
        return min(1.0, score)


# --- ALIGNMENT GATE ---
class AlignmentGate(BaseGate):
    '''Triadic energy-information-consciousness alignment heuristic.'''
    def __init__(self, name, ref_vectors=None, threshold=0.7, weight=1.5, critical=True):
        super().__init__(name, threshold, weight, critical)
        self.ref_vectors = ref_vectors or [0.707, 0.618, 0.786]

    def evaluate(self, payload):
        txt = (payload.get('human_text', '') + payload.get('ai_text', '')).lower()
        # heuristic triadic pattern scan
        triad_terms = ['energy', 'information', 'consciousness']
        matches = sum(term in txt for term in triad_terms)
        base_score = matches / len(triad_terms)
        # harmonic modulation via reference vectors
        harmonic = sum(self.ref_vectors) / len(self.ref_vectors)
        score = base_score * harmonic
        # slight stochastic resonance factor
        jitter = random.uniform(-0.02, 0.02)
        return max(0, min(1, score + jitter))
