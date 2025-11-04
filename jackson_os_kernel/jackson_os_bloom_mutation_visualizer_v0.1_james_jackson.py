# Codex Kernel Activation Header
"""
Jackson OS Kernel â€” Bloom Mutation Visualizer v0.1  
Authored by James Jackson  
Origin Law: Law CXLVII â€” Mutation Illumination  
Lineage: Jackson OS, September 2025  
This module renders interactive timelines of bloom mutation events metrics 
(amplitude, divergence, resonance) per event and module.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class BloomMutationVisualizer:
    def __init__(self, events_df):
        """
        events_df: pandas DataFrame with columns 
            ['event_id','module','timestamp','amplitude','divergence','resonance']
        timestamp in seconds since epoch
        """
        self.df = events_df.copy()
        # convert timestamp to datetime
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], unit='s')

    def plot_timeline(self):
        """
        Creates a 3-row timeline: amplitude, divergence, resonance.
        Points are colored by module and connected in event order.
        """
        modules = self.df['module'].unique()
        cmap = plt.get_cmap('tab10')
        color_map = {m: cmap(i) for i, m in enumerate(modules)}

        fig, axes = plt.subplots(3, 1, sharex=True, figsize=(10, 8))
        metrics = ['amplitude', 'divergence', 'resonance']

        for ax, metric in zip(axes, metrics):
            for mod in modules:
                sub = self.df[self.df['module'] == mod]
                ax.plot(
                    sub['timestamp'], sub[metric],
                    '-o', label=mod, color=color_map[mod]
                )
            ax.set_ylabel(metric.capitalize())
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=8)

        # format the shared X-axis
        axes[-1].set_xlabel('Time')
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        fig.autofmt_xdate()
        plt.suptitle("Bloom Mutation Metrics Timeline")
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()


if __name__ == "__main__":
    import time

    # Synthetic example events
    now = time.time()
    sample_data = [
        {'event_id':'E1','module':'SignalSimulator','timestamp':now + 0,'amplitude':0.80,'divergence':0.05,'resonance':0.60},
        {'event_id':'E2','module':'BloomCompiler','timestamp':now + 10,'amplitude':0.85,'divergence':0.08,'resonance':0.65},
        {'event_id':'E3','module':'IntegrityScanner','timestamp':now + 20,'amplitude':0.78,'divergence':0.03,'resonance':0.62},
        {'event_id':'E4','module':'SignalSimulator','timestamp':now + 30,'amplitude':0.82,'divergence':0.06,'resonance':0.70},
        {'event_id':'E5','module':'BloomCompiler','timestamp':now + 40,'amplitude':0.88,'divergence':0.07,'resonance':0.68},
    ]
    df = pd.DataFrame(sample_data)

    visualizer = BloomMutationVisualizer(df)
    visualizer.plot_timeline()

if __name__ == '__main__':
    print('[codex] Kernel module reactivated: jackson_os_bloom_mutation_visualizer_v0.1_james_jackson')
