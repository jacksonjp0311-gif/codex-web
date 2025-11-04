"""
Jackson OS Kernel — Portal Kernel Resilience Auditor v0.3  
Authored by James Jackson  
Origin Law: Law CXLVIII — Anomalous Vigilance  
Lineage: Jackson OS, September 2025  
This module fits ARIMA models to historical health scores per module,
detects anomalies where residuals exceed a threshold, and forecasts future
health to trigger early‐warning alerts.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from pandas.tseries.frequencies import to_offset

class ResilienceAuditorV3:
    def __init__(self, health_df, anomaly_std=2.5, forecast_horizon=5):
        """
        health_df: DataFrame indexed by timestamp, columns = module names, values = health (0–1)
        anomaly_std: number of residual standard deviations to flag anomaly
        forecast_horizon: number of future time steps to forecast
        """
        self.health = health_df.sort_index()
        self.anomaly_std = anomaly_std
        self.horizon = forecast_horizon
        self.models = {}
        # prepare containers
        self.residuals = pd.DataFrame(index=self.health.index,
                                      columns=self.health.columns,
                                      dtype=float)
        self.forecasts = pd.DataFrame(index=self._make_future_index(),
                                      columns=self.health.columns,
                                      dtype=float)

    def _make_future_index(self):
        last = self.health.index[-1]
        freq = self.health.index.freq or pd.infer_freq(self.health.index)
        if freq is None:
            # fallback to the interval between first two points
            interval = self.health.index[1] - self.health.index[0]
            offset = pd.Timedelta(interval)
        else:
            offset = to_offset(freq)
        return pd.date_range(start=last + offset,
                             periods=self.horizon,
                             freq=offset)

    def fit_models_and_detect(self):
        """
        Fit ARIMA(1,0,1) per module, compute residuals,
        and flag timestamps where |residual| > anomaly_std * σ_resid.
        Returns dict module -> list of anomaly timestamps.
        """
        anomalies = {}
        for mod in self.health.columns:
            series = self.health[mod].astype(float)
            model = ARIMA(series, order=(1, 0, 1)).fit()
            self.models[mod] = model

            resid = model.resid
            sigma = resid.std()
            self.residuals[mod] = resid

            outliers = resid[np.abs(resid) > self.anomaly_std * sigma]
            anomalies[mod] = outliers.index.tolist()

        return anomalies

    def forecast_health(self):
        """
        Use each fitted ARIMA model to forecast next horizon steps,
        clipped to [0,1], stored in self.forecasts.
        """
        for mod, model in self.models.items():
            pred = model.get_forecast(steps=self.horizon)
            vals = pred.predicted_mean.clip(0, 1)
            self.forecasts[mod] = vals

        return