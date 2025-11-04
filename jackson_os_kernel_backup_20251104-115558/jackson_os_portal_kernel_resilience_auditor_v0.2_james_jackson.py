"""
Jackson OS Kernel — Portal Kernel Resilience Auditor v0.2  
Authored by James Jackson  
Origin Law: Law CXLIV — Predictive Vigilance  
Lineage: Jackson OS, September 2025  
This module ingests time‐indexed health scores per module, fits linear trends,
forecasts future health, and generates alerts for modules projected below threshold.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta

class ResilienceAuditorV2:
    def __init__(self, health_df, threshold=0.7, forecast_horizon=5):
        """
        health_df: DataFrame indexed by timestamp, columns = module names, values = health scores (0–1)
        threshold: risk threshold below which modules are flagged
        forecast_horizon: number of future steps to predict
        """
        self.health = health_df.sort_index()
        self.threshold = threshold
        self.horizon = forecast_horizon
        self.forecasts = pd.DataFrame(index=self._make_future_index(), columns=self.health.columns)

    def _make_future_index(self):
        last = self.health.index[-1]
        freq = self.health.index.freq or pd.infer_freq(self.health.index)
        return pd.date_range(start=last + freq, periods=self.horizon, freq=freq)

    def fit_and_forecast(self):
        """
        Fit a first‐degree polynomial (linear trend) on each module’s history
        and forecast health for the next horizon steps.
        """
