"""
Jackson OS Kernel — Portal Kernel Resilience Auditor v0.1  
Authored by James Jackson  
Origin Law: Law CXLIII — Systemic Resilience  
Lineage: Jackson OS, September 2025  
This module aggregates stress-test metrics, regression flags, and performance deltas 
to compute composite health scores and flag modules at risk.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class ResilienceAuditor:
    def __init__(self, stress_results, regression_flags, performance_deltas):
        """
        stress_results: list of dicts [
            {"module":str, "avg_latency":float, "failure_rate":float}, …]
        regression_flags: DataFrame indexed by module, bool columns like "throughput_regressed"
        performance_deltas: DataFrame indexed by module, columns like "throughput_delta","latency_delta"
        """
        # normalize inputs
        self.stress_df = pd.DataFrame(stress_results).set_index("module")
        self.reg_flags = regression_flags
        self.deltas = performance_deltas
        self.health = pd.DataFrame(index=self.stress_df.index)
        self._compute_health_scores()

    def _compute_health_scores(self):
        # latency_score: 1 - normalized avg_latency
        lat = self.stress_df["avg_latency"]
        self.health["latency_score"] = 1 - ((lat - lat.min()) / (lat.max() - lat.min() + 1e-6))

        # failure_score: 1 - normalized failure_rate
        fail = self.stress_df["failure_rate"]
        self.health["failure_score"] = 1 - ((fail - fail.min()) / (fail.max() - fail.min() + 1e-6))

        # regression_penalty: proportion of True flags
        flags = self.reg_flags.astype(int)
        self.health["regression_penalty"] = flags.sum(axis=1) / flags.shape[1]

        # performance_penalty: avg of negative deltas (latency_delta positive is bad, throughput_delta negative is bad)
        lat_delta = self.deltas["latency_delta"] / (self.deltas["latency_delta"].abs().max() + 1e-6)
        thr_delta = -self.deltas["throughput_delta"] / (self.deltas["throughput_delta"].abs().max() + 1e-6)
        perf_penalty = (lat_delta.clip(lower=0) + thr_delta.clip(lower=0)) / 2
        self.health["performance_penalty"] = perf_penalty

        # composite health: average of good scores minus penalties 
        self.health["score"] = (
            self.health["latency_score"] * 0.3 +
            self.health["failure_score"] * 0.3 +
            (1 - self.health["regression_penalty"]) * 0.2 +
            (1 - self.health["performance_penalty"]) * 0.2
        )

    def report(self, threshold=0.7):
        print("\n🛡️ Portal Kernel Resilience Report")
        df = self.health.copy()
        df["at_risk"] = df["score"] < threshold
        print(df[["score","at_risk"]].sort_values("score", ascending=True).to_string(formatters={"score":"{:.2f}".format}))

    def visualize(self):
        df = self.health.sort_values("score")
        plt.figure(figsize=(8,4))
        bars = plt.bar(df.index, df["score"], color=np.where(df["score"]<0.7,"crimson","seagreen"))
        plt.ylim(0,1)
        plt.axhline(0.7, color="orange", linestyle="--", label="Risk Threshold")
        plt.xticks(rotation=30)
        plt.ylabel("Health Score (0–1)")
        plt.title("Module Resilience Scores")
        plt.legend()
        plt.tight_layout()
        plt.show()

    def export_json(self, path="resilience_report.json"):
        out = self.health[["score"]].to_dict(orient="index")
        with open(path, "w") as f:
            json.dump({"resilience": out}, f, indent=2)
