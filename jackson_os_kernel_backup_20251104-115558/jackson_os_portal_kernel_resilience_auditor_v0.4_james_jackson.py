"""
Jackson OS Kernel — Portal Kernel Resilience Auditor v0.4  
Authored by James Jackson  
Origin Law: Law CLII — Bayesian Vigilance  
Lineage: Jackson OS, September 2025  
This module detects Bayesian changepoints in each module’s health history  
using offline RBF‐based segmentation, then fits ARIMA models for short‐term  
forecasting to issue early alerts on potential degradations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ruptures as rpt
from statsmodels.tsa.arima.model import ARIMA

class ResilienceAuditorV4:
    def __init__(self, health_df, penalty=3, forecast_horizon=8):
        """
        health_df: DataFrame indexed by timestamp, columns=module names, values=health (0–1)
        penalty: penalty parameter for RBF changepoint detection
        forecast_horizon: number of future points to forecast
        """
        self.health = health_df.sort_index().astype(float)
        self.penalty = penalty
        self.horizon = forecast_horizon

        # containers
        self.change_points = {}     # module -> list of datetime indices
        self.forecasts = pd.DataFrame(
            index=self._make_future_index(), 
            columns=self.health.columns,
            dtype=float
        )

    def _make_future_index(self):
        freq = self.health.index.freq or pd.infer_freq(self.health.index)
        return pd.date_range(
            start=self.health.index[-1] + (freq or self.health.index[1] - self.health.index[0]),
            periods=self.horizon,
            freq=freq
        )

    def detect_changepoints(self):
        """
        For each module, apply offline RBF segmentation to find breakpoints.
        Stores change points in self.change_points.
        Returns dict module->list of timestamps.
        """
        for mod in self.health.columns:
            series = self.health[mod].values
            algo = rpt.Pelt(model="rbf").fit(series)
            # find breakpoints; last index is length of series, drop it
            bkps = algo.predict(pen=self.penalty)[:-1]
            times = [self.health.index[i] for i in bkps]
            self.change_points[mod] = times
        return self.change_points

    def forecast_health(self):
        """
        Fit ARIMA(1,0,1) per module, forecast next horizon points,
        clip to [0,1], store in self.forecasts.
        Returns forecasts DataFrame.
        """
        for mod in self.health.columns:
            model = ARIMA(self.health[mod], order=(1,0,1)).fit()
            pred = model.get_forecast(steps=self.horizon)
            vals = pred.predicted_mean.clip(0,1)
            self.forecasts[mod] = vals
        return self.forecasts

    def visualize(self, module):
        """
        Plot history with changepoints, and forecast as dashed line.
        """
        idx = self.health.index
        hist = self.health[module]
        cp = self.change_points.get(module, [])
        fut_idx = self.forecasts.index
        fut = self.forecasts[module]

        plt.figure(figsize=(10,4))
        plt.plot(idx, hist, label="Historical", color="teal")
        for t in cp:
            plt.axvline(t, color="crimson", linestyle="--", alpha=0.7)
        plt.plot(fut_idx, fut, "--", color="darkorange", label="Forecast")
        plt.title(f"Resilience Audit v0.4 — {module}")
        plt.xlabel("Time")
        plt.ylabel("Health Score (0–1)")
        plt.legend(loc="upper right", fontsize=8)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # synthetic demo data
    idx = pd.date_range("2025-09-23", periods=60, freq="H")
    data = {
        "SignalSim":      0.9 + 0.02*np.random.randn(60).cumsum(),
        "BloomCompile":   0.85 + 0.015*np.random.randn(60).cumsum(),
        "IntegrityScan":  0.95 - 0.02*np.random.randn(60).cumsum(),
    }
    health_df = pd.DataFrame(data, index=idx).clip(0,1)

    auditor = ResilienceAuditorV4(health_df, penalty=4, forecast_horizon=12)
    cps = auditor.detect_changepoints()
    forecasts = auditor.forecast_health()

    print("\n🔍 Detected Changepoints")
    for mod, times in cps.items():
        print(f"{mod}: {len(times)} changes at {times}")

    auditor.visualize("SignalSim")
