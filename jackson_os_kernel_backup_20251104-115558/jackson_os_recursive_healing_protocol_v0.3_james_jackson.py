"""
Jackson OS Kernel — Recursive Healing Protocol v0.3  
Authored by James Jackson  
Origin Law: Law CXLII — Learned Autonomy  
Lineage: Jackson OS, September 2025  
This module monitors drift anomalies and, once trained on past outcomes, uses 
a Decision Tree to predict heal actions. Thresholds adapt via ML instead of fixed rules.
"""

import time
import uuid
import logging
from collections import defaultdict
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

# configure logger
logger = logging.getLogger("HealingProtocolV3")
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler("healing_protocol_v0.3.log"))

# record of each anomaly & heal decision
class HealEventRecord:
    def __init__(self, module, drift, threshold, healed):
        self.module = module
        self.drift = drift
        self.threshold = threshold
        self.healed = healed
        self.timestamp = time.time()

# healing protocol v0.3
class HealingProtocolV3:
    def __init__(self, reset_functions, adapt_rate=0.1, min_train=20):
        """
        reset_functions: dict module_name->callable
        adapt_rate: same as v0.2, for initial thresholding
        min_train: min events before ML kicks in
        """
        self.resets = reset_functions
        self.adapt_rate = adapt_rate
        self.min_train = min_train
        self.history = []  # list of HealEventRecord
        self.model = None

    def _adaptive_threshold(self, anomaly, heal_count):
        return anomaly.base_threshold * (1 + self.adapt_rate * heal_count)

    def _train_model(self):
        df = pd.DataFrame([{
            "drift": r.drift,
            "threshold": r.threshold,
            "healed": int(r.healed)
        } for r in self.history])
        X = df[["drift", "threshold"]]
        y = df["healed"]
        clf = DecisionTreeClassifier(max_depth=3, random_state=42)
        clf.fit(X, y)
        self.model = clf
        logger.info(f"🚀 Trained ML model on {len(df)} events")

    def heal(self, anomalies):
        report = []
        # count past heals per module
        heal_counts = defaultdict(int)
        for r in self.history:
            if r.healed:
                heal_counts[r.module] += 1

        # trigger ML training if enough history
        if len(self.history) >= self.min_train and self.model is None:
            self._train_model()

        for anom in anomalies:
            base_thresh = self._adaptive_threshold(anom, heal_counts[anom.module])
            use_ml = self.model is not None
            if use_ml:
                X_new = [[anom.drift, base_thresh]]
                p_heal = self.model.predict_proba(X_new)[0][1]
                do_heal = (p_heal > 0.5)
            else:
                # fallback to v0.2 deterministic + prob
                excess = anom.drift - base_thresh
                p_heal = min(max(excess/(anom.drift+1e-6), 0), 1)
                do_heal = anom.drift > base_thresh and time.time()%1 < p_heal

            if do_heal:
                self.resets.get(anom.module, lambda: None)()
                logger.info(f"⚕️ Healed {anom.module} | drift={anom.drift:.3f} "
                            f"thresh={base_thresh:.3f} p_heal={p_heal:.2f}")
            else:
                logger.info(f"✅ Skipped heal for {anom.module} | drift={anom.drift:.3f} "
                            f"thresh={base_thresh:.3f} p_heal={p_heal:.2f}")

            # record event
            self.history.append(HealEventRecord(
                anom.module, anom.drift, base_thresh, do_heal
            ))
            report.append({
                "module": anom.module,
                "drift": anom.drift,
                "threshold": base_thresh,
                "p_heal": p_heal,
                "healed": do_heal
            })

        return report

# example anomaly class unchanged from v0.2
class DriftAnomaly:
    def __init__(self, module_name, drift_score, base_threshold):
        self.module = module_name
        self.drift = drift_score
        self.base_threshold = base_threshold
        self.timestamp = time.time()

if __name__ == "__main__":
    import random

    # example resets
    def reset_sim():
        print("  • Resetting Feedback Simulator.")

    resets = {"FeedbackSimulator": reset_sim}

    protocol = HealingProtocolV3(resets, adapt_rate=0.1, min_train=5)

    # simulate anomalies
    for step in range(15):
        anom = DriftAnomaly("FeedbackSimulator",
                            drift_score=random.uniform(0.0,0.5),
                            base_threshold=0.2)
        report = protocol.heal([anom])
        print(f"Step {step+1}: {report[-1]}")
        time.sleep(0.1)

    # after enough events, ML model trains and influences decisions
