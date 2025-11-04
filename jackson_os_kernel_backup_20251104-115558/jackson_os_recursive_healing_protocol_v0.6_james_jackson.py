"""
Jackson OS Kernel — Recursive Healing Protocol v0.6  
Authored by James Jackson  
Origin Law: Law CLIV — Traced Planning  
Lineage: Jackson OS, October 2025  
This module extends v0.5 with multi‐step temporal‐difference learning  
and eligibility traces (SARSA(λ)) to accelerate convergence on good heal thresholds.
"""

import time
import random
import logging
import numpy as np
from collections import defaultdict

# configure logger
logger = logging.getLogger("HealingProtocolV6")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("healing_protocol_v0.6.log")
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class DriftAnomaly:
    def __init__(self, module_name, drift_score, base_threshold):
        self.module = module_name
        self.drift = drift_score
        self.base_threshold = base_threshold
        self.timestamp = time.time()


class HealingProtocolV6:
    def __init__(
        self,
        reset_functions,
        actions=(0.8, 1.0, 1.2, 1.5),
        alpha=0.05,
        gamma=0.9,
        lamda=0.8,
        epsilon=0.2
    ):
        """
        reset_functions: dict module_name -> callable  
        actions: tuple of threshold multipliers  
        alpha: learning rate  
        gamma: discount factor  
        lamda: eligibility‐trace decay  
        epsilon: exploration probability  
        """
        self.resets = reset_functions
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.lamda = lamda
        self.epsilon = epsilon

        # weights & traces: module -> {action: np.array([w0,w1,w2])}
        self.weights = defaultdict(
            lambda: {a: np.zeros(3, dtype=float) for a in self.actions}
        )
        self.eligibility = defaultdict(
            lambda: {a: np.zeros(3, dtype=float) for a in self.actions}
        )
        self.heal_counts = defaultdict(int)

    def _features(self, anomaly):
        """Feature vector [drift, base_threshold, heal_count]."""
        count = self.heal_counts[anomaly.module]
        return np.array([anomaly.drift, anomaly.base_threshold, count], dtype=float)

    def _select_action(self, module, feats):
        """ε-greedy policy."""
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        qvals = {
            a: float(np.dot(w, feats))
            for a, w in self.weights[module].items()
        }
        return max(qvals, key=qvals.get)

    def heal(self, anomalies):
        """
        anomalies: list of DriftAnomaly  
        Processes each anomaly sequentially, updating weights via SARSA(λ).
        Returns list of decision reports.
        """
        reports = []
        # clear eligibility traces at start of batch
        for tr in self.eligibility.values():
            for a in tr:
                tr[a].fill(0.0)

        next_feats = None
        next_action = None

        for idx, anom in enumerate(anomalies):
            feats = self._features(anom)
            action = (
                next_action
                if idx > 0
                else self._select_action(anom.module, feats)
            )
            # Q-value for current state‐action
            Q_curr = np.dot(self.weights[anom.module][action], feats)

            # decision & reward
            thresh = anom.base_threshold * action
            do_heal = anom.drift > thresh
            ideal = anom.drift > anom.base_threshold
            reward = 1.0 if do_heal == ideal else -1.0

            # perform heal
            if do_heal:
                fn = self.resets.get(anom.module)
                if callable(fn):
                    fn()
                self.heal_counts[anom.module] += 1
                logger.info(
                    f"Healed {anom.module} | drift={anom.drift:.3f} "
                    f"thresh={thresh:.3f}×{action:.1f} | reward={reward:.1f}"
                )
            else:
                logger.info(
                    f"Skipped {anom.module} | drift={anom.drift:.3f} "
                    f"thresh={thresh:.3f}×{action:.1f} | reward={reward:.1f}"
                )

            # select next action & features for SARSA
            if idx < len(anomalies) - 1:
                next_feats = self._features(anomalies[idx + 1])
                next_action = self._select_action(anom.module, next_feats)
                Q_next = np.dot(self.weights[anom.module][next_action], next_feats)
            else:
                Q_next = 0.0

            # TD error
            delta = reward + self.gamma * Q_next - Q_curr

            # update eligibility for this action
            self.eligibility[anom.module][action] = (
                self.gamma * self.lamda * self.eligibility[anom.module][action]
                + feats
            )

            # update all weights
            for a in self.actions:
                self.weights[anom.module][a] += (
                    self.alpha
                    * delta
                    * self.eligibility[anom.module][a]
                )
                # decay trace
                self.eligibility[anom.module][a] *= self.gamma * self.lamda

            reports.append({
                "module": anom.module,
                "drift": anom.drift,
                "multiplier": action,
                "threshold": thresh,
                "healed": do_heal,
                "reward": reward
            })

        return reports


if __name__ == "__main__":
    # example reset function
    def reset_simulator():
        print("  • Resetting Feedback Simulator.")

    resets = {"FeedbackSimulator": reset_simulator}

    protocol = HealingProtocolV6(
        reset_functions=resets,
        actions=(0.8, 1.0, 1.2),
        alpha=0.1,
        gamma=0.9,
        lamda=0.8,
        epsilon=0.3
    )

    # simulate a batch of anomalies
    batch = [
        DriftAnomaly("FeedbackSimulator", random.uniform(0,0.6), 0.2)
        for _ in range(20)
    ]
    reports = protocol.heal(batch)
    for i, rep in enumerate(reports, 1):
        print(f"Step {i}: {rep}")
        time.sleep(0.1)
