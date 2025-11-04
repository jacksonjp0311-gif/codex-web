"""
Jackson OS Kernel — Recursive Healing Protocol v0.5  
Authored by James Jackson  
Origin Law: Law CL — Function-Approximated Autonomy  
Lineage: Jackson OS, September 2025  
This module uses a linear value-function approximator (weights per action)  
to select heal-threshold multipliers, updating weights via temporal-difference  
learning on each anomaly event.
"""

import time
import random
import logging
import numpy as np
from collections import defaultdict

# configure logger
logger = logging.getLogger("HealingProtocolV5")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("healing_protocol_v0.5.log")
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class DriftAnomaly:
    def __init__(self, module_name, drift_score, base_threshold):
        self.module = module_name
        self.drift = drift_score
        self.base_threshold = base_threshold
        self.timestamp = time.time()


class HealingProtocolV5:
    def __init__(
        self,
        reset_functions,
        actions=(0.8, 1.0, 1.2, 1.5),
        alpha=0.05,
        epsilon=0.2
    ):
        """
        reset_functions: dict module_name -> callable
        actions: tuple of threshold multipliers
        alpha: learning rate
        epsilon: exploration probability
        """
        self.resets = reset_functions
        self.actions = actions
        self.alpha = alpha
        self.epsilon = epsilon

        # weights per module per action (feature dims = 3)
        self.weights = defaultdict(
            lambda: {a: np.zeros(3, dtype=float) for a in self.actions}
        )
        # count of heals performed per module
        self.heal_counts = defaultdict(int)

    def _features(self, anomaly):
        """[drift, base_threshold, heal_count] as feature vector."""
        count = self.heal_counts[anomaly.module]
        return np.array([anomaly.drift, anomaly.base_threshold, count], dtype=float)

    def _select_action(self, module, feats):
        """Epsilon-greedy: explore with prob ε, else pick highest Q."""
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        qvals = {
            a: float(np.dot(w, feats))
            for a, w in self.weights[module].items()
        }
        return max(qvals, key=qvals.get)

    def _update_weights(self, module, action, reward, feats):
        """TD update: w ← w + α·(reward − Q)·features."""
        w = self.weights[module][action]
        q_old = float(np.dot(w, feats))
        td_err = reward - q_old
        self.weights[module][action] = w + self.alpha * td_err * feats

    def heal(self, anomalies):
        """
        anomalies: list of DriftAnomaly
        Returns list of dicts with decision & reward details.
        """
        reports = []
        for anom in anomalies:
            feats = self._features(anom)
            mult = self._select_action(anom.module, feats)
            thresh = anom.base_threshold * mult
            do_heal = anom.drift > thresh

            # ideal: heal iff drift > base_threshold
            ideal = anom.drift > anom.base_threshold
            reward = 1.0 if do_heal == ideal else -1.0

            if do_heal:
                reset_fn = self.resets.get(anom.module)
                if callable(reset_fn):
                    reset_fn()
                self.heal_counts[anom.module] += 1
                logger.info(
                    f"Healed {anom.module} | drift={anom.drift:.3f} "
                    f"thresh={thresh:.3f}×{mult:.1f} | reward={reward:.1f}"
                )
            else:
                logger.info(
                    f"Skipped {anom.module} | drift={anom.drift:.3f} "
                    f"thresh={thresh:.3f}×{mult:.1f} | reward={reward:.1f}"
                )

            self._update_weights(anom.module, mult, reward, feats)

            reports.append({
                "module": anom.module,
                "drift": anom.drift,
                "multiplier": mult,
                "threshold": thresh,
                "healed": do_heal,
                "reward": reward
            })

        return reports


if __name__ == "__main__":
    # example reset functions
    def reset_simulator():
        print("  • Resetting Feedback Simulator.")

    resets = {"FeedbackSimulator": reset_simulator}

    protocol = HealingProtocolV5(
        reset_functions=resets,
        actions=(0.8, 1.0, 1.2),
        alpha=0.1,
        epsilon=0.3
    )

    # drive with synthetic anomalies
    for step in range(1, 16):
        drift = random.uniform(0.0, 0.6)
        anom = DriftAnomaly(
            module_name="FeedbackSimulator",
            drift_score=drift,
            base_threshold=0.2
        )
        report = protocol.heal([anom])
        print(f"Step {step}: {report[-1]}")
        time.sleep(0.2)

