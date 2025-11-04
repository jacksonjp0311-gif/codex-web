"""
Jackson OS Kernel — Temporal–Topological Analyzer v0.1  
Authored by James Jackson  
Origin Law: Law CXXXVIII — Temporal–Topological Correlation  
Lineage: Jackson OS, September 2025  
This module correlates network performance logs with bloom mutation metrics 
over time, revealing synchronous patterns and propagation lags.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class TemporalTopologicalAnalyzer:
    def __init__(self, network_df, bloom_df, window_size=50, max_lag=20):
        """
        network_df: DataFrame indexed by timestamp with columns ['throughput','latency','error_rate']
        bloom_df:   DataFrame indexed by timestamp with columns ['amplitude','divergence','resonance']
        window_size: sliding window length for rolling correlation
        max_lag: maximum lag (in steps) for cross-correlation analysis
        """
        # align on timestamps
        self.data = pd.concat([network_df, bloom_df], axis=1).dropna()
        self.window = window_size
        self.max_lag = max_lag

    def compute_rolling_correlation(self):
        """Compute rolling-window Pearson correlations between all metric pairs."""
        return self.data.rolling(self.window).corr().dropna()

    def compute_cross_correlations(self):
        """
        Compute cross-correlation series for each network vs bloom metric pair.
        Returns dict of {(net_col, bloom_col): corr_series}
        """
        cc_dict = {}
        net_cols = ['throughput','latency','error_rate']
        bloom_cols = ['amplitude','divergence','resonance']
        for n in net_cols:
            for b in bloom_cols:
                series_n = self.data[n] - self.data[n].mean()
                series_b = self.data[b] - self.data[b].mean()
                corr = [series_n.corr(series_b.shift(lag)) for lag in range(-self.max_lag, self.max_lag+1)]
                cc_dict[(n, b)] = np.array(corr)
        return cc_dict

    def visualize_heatmap(self):
        """Plot a single heatmap of correlations at the final window."""
        corr_matrix = self.compute_rolling_correlation().xs(self.data.columns[0], level=0).iloc[-len(self.data.columns):]
        plt.figure(figsize=(6,5))
        sns.heatmap(corr_matrix, annot=True, cmap='vlag', center=0)
        plt.title("Rolling Correlation (last window)")
        plt.tight_layout()
        plt.show()

    def visualize_cross_correlation(self):
        """Plot cross-correlation curves for each metric pair."""
        cc = self.compute_cross_correlations()
        lags = np.arange(-self.max_lag, self.max_lag+1)
        plt.figure(figsize=(8,6))
        for (n,b), series in cc.items():
            plt.plot(lags, series, label=f"{n}↔{b}")
        plt.axvline(0, color='k', linestyle='--', alpha=0.5)
        plt.title("Cross-Correlation (network vs bloom)")
        plt.xlabel("Lag steps (positive ⇒ network leads)")
        plt.ylabel("Correlation")
        plt.legend(fontsize=8, ncol=2)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    # Synthetic example data
    idx = pd.date_range(start="2025-09-23", periods=200, freq="T")
    network_df = pd.DataFrame({
        'throughput': np.sin(np.linspace(0,4*np.pi,200)) + 5 + 0.5*np.random.randn(200),
        'latency':    np.cos(np.linspace(0,4*np.pi,200)) * 0.02 + 0.05*np.random.randn(200),
        'error_rate': np.abs(0.1*np.sin(np.linspace(0,2*np.pi,200)) + 0.05*np.random.randn(200))
    }, index=idx)

    bloom_df = pd.DataFrame({
        'amplitude':  np.sin(np.linspace(0,4*np.pi,200)) * (1 + 0.1*np.random.randn(200)),
        'divergence': np.abs(0.05*np.cos(np.linspace(0,4*np.pi,200)) + 0.02*np.random.randn(200)),
        'resonance':  np.sin(np.linspace(0,2*np.pi,200)) * 0.5 + 0.5*np.random.randn(200)
    }, index=idx)

    analyzer = TemporalTopologicalAnalyzer(network_df, bloom_df, window_size=30, max_lag=15)
    analyzer.visualize_heatmap()
    analyzer.visualize_cross_correlation()
