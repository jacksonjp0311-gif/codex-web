"""
Jackson OS Kernel — Performance Regression Tester v0.1  
Authored by James Jackson  
Origin Law: Law CXLI — Comparative Transparency  
Lineage: Jackson OS, September 2025  
This module compares baseline vs tuned performance logs, quantifies metric shifts,
identifies regressions, and renders comparative visualizations.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class PerformanceRegressionTester:
    def __init__(self, baseline_logs, tuned_logs, metrics=None):
        """
        baseline_logs, tuned_logs: list of dicts 
            e.g. [{"module":"X","throughput":…,"latency":…,"error_rate":…}, …]
        metrics: list of metric names to compare; defaults to all numeric keys except "module"
        """
        self.baseline = pd.DataFrame(baseline_logs)
        self.tuned    = pd.DataFrame(tuned_logs)
        self.metrics = metrics or [c for c in self.baseline.columns if c != "module"]
        self._align_modules()

    def _align_modules(self):
        # ensure both contain same modules
        common = set(self.baseline["module"]) & set(self.tuned["module"])
        self.baseline = self.baseline[self.baseline["module"].isin(common)]
        self.tuned    = self.tuned[self.tuned["module"].isin(common)]

    def compute_deltas(self):
        """Compute mean delta and percent change per module/metric."""
        base_grp = self.baseline.groupby("module")[self.metrics].mean()
        tune_grp = self.tuned.groupby("module")[self.metrics].mean()
        delta = tune_grp - base_grp
        pct   = (delta / base_grp.replace(0, pd.NA)) * 100
        self.results = delta.join(pct, lsuffix="_delta", rsuffix="_pct")
        return self.results

    def identify_regressions(self, thresholds):
        """
        thresholds: dict metric -> percent-change threshold beyond which
            positive pct indicates regression for latency and error_rate,
            negative pct indicates regression for throughput.
        Returns DataFrame of flags.
        """
        pct_cols = [m+"_pct" for m in self.metrics]
        flags = pd.DataFrame(index=self.results.index)
        for m in self.metrics:
            col = m + "_pct"
            thresh = thresholds.get(m, 0)
            if m in ("latency","error_rate"):
                flags[m+"_regressed"] = self.results[col] > thresh
            else:  # throughput
                flags[m+"_regressed"] = self.results[col] < -abs(thresh)
        self.regressions = flags
        return flags

    def report(self):
        """Print tabular summary of deltas and regression flags."""
        df = self.results.join(self.regressions)
        print("\n🛠️ Performance Regression Report")
        print(df.style.format("{:.2f}").to_string())

    def visualize(self):
        """Barplot of percent changes per module/metric."""
        pct = self.results[[m+"_pct" for m in self.metrics]].copy()
        pct.columns = self.metrics
        pct = pct.reset_index().melt(id_vars="module", var_name="metric", value_name="% change")
        plt.figure(figsize=(8,4))
        sns.barplot(data=pct, x="module", y="% change", hue="metric")
        plt.axhline(0, color="k", linestyle="--", alpha=0.6)
        plt.title("Pre vs Tuned Performance % Change")
        plt.ylabel("Percent Change")
        plt.xlabel("Module")
        plt.legend(loc="upper right")
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # Example log entries
    baseline_logs = [
        {"module":"Law-Signal Feedback Simulator","throughput":12.5,"latency":0.03,"error_rate":0.02},
        {"module":"Recursive Bloom Compiler","throughput":10.2,"latency":0.04,"error_rate":0.03},
        {"module":"Portal-Kernel Integrity Scanner","throughput":15.0,"latency":0.02,"error_rate":0.01},
    ]
    tuned_logs = [
        {"module":"Law-Signal Feedback Simulator","throughput":11.0,"latency":0.025,"error_rate":0.025},
        {"module":"Recursive Bloom Compiler","throughput":10.8,"latency":0.045,"error_rate":0.02},
        {"module":"Portal-Kernel Integrity Scanner","throughput":15.5,"latency":0.018,"error_rate":0.015},
    ]

    tester = PerformanceRegressionTester(baseline_logs, tuned_logs)
    tester.compute_deltas()
    tester.identify_regressions({"throughput":5,"latency":5,"error_rate":2})
    tester.report()
    tester.visualize()
