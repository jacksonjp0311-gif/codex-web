# =========================================================
# Codex Fractal Seal — Protocol Specification (v0.2)
# Author: James Paul Jackson
# Purpose: Core triadic framework validation and seal synchronization controller
# =========================================================

import hashlib, json, time

class CodexSeal:
    def __init__(self):
        self.version = "0.2"
        self.timestamp = time.time()
        self.signature = None

    def encode_triad(self, data):
        combined = json.dumps(data, sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()[:12]

    def seal(self, data):
        triad_key = self.encode_triad(data)
        self.signature = f"CFS-{triad_key}-{self.version}"
        return self.signature

    def verify(self, data):
        expected = f"CFS-{self.encode_triad(data)}-{self.version}"
        return expected == self.signature


# =========================================================
# SealController — manages gates + triadic synchronization
# =========================================================

class SealController:
    def __init__(self, gates=None, global_threshold=0.7):
        self.gates = gates or []
        self.global_threshold = global_threshold
        self.seal = CodexSeal()

    def sync_and_adjust(self, payload, max_cycles=3, cooldown=0.1):
        results = []
        G = 0.0
        for cycle in range(max_cycles):
            total_weight = 0
            score = 0
            for gate in self.gates:
                val = gate.evaluate(payload)
                score += val * gate.weight
                total_weight += gate.weight
            avg = score / total_weight if total_weight else 0
            results.append(avg)
            if avg >= self.global_threshold:
                sig = self.seal.seal(payload)
                return True, {'signature': sig, 'results': results, 'G': avg}
            time.sleep(cooldown)
        return False, {'results': results, 'G': avg}
