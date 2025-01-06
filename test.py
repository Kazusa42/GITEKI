import os
import re
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class TracePlot:
    def __init__(self, trace_dir='trace_data'):
        self.trace_files = [
            f for f in os.listdir(trace_dir) if f.startswith('trace')
        ]
        self._verify_data_integrity()

    def _verify_data_integrity(self, p_end=r'~([\d.]+)\.csv', p_start=r'_([\d.]+)~'):
        trace_files = sorted(self.trace_files,
                             key=lambda name: float(re.search(p_start, name).group(1)))
        for idx in range(len(trace_files) - 1):
            curr_end = re.search(p_end, trace_files[idx]).group(1)
            next_start = re.search(p_start, trace_files[idx + 1]).group(1)
            if curr_end != next_start:
                missing_freq = f"{curr_end}~{next_start}"
                raise FileNotFoundError(f"Missing trace for freq range: {missing_freq}")
        self.trace_files = trace_files
            
    def _load_data(self, trace_dir):
        density, all_data = float('inf'), []
        for f in self.trace_files:
            df = pd.read_csv(os.path.join(trace_dir, f))
            df = df.apply(pd.to_numeric, errors='coerce')
            h_idx = df[0].apply(pd.to_numeric, errors='coerce').first_valid_index()
            data = df.iloc[h_idx:, :2]
            data.iloc[:, 0] /= 1e9  # Convert freq to GHz
            all_data.append(data)

            start_freq, end_freq = data.iloc[0, 0], data.iloc[-1, 0]
            t_density = (len(data) * 1e6) / (end_freq - start_freq)
            density = min(t_density, density)
        
        sampled_data = []
        for data in all_data:
            start_freq, end_freq = data.iloc[0, 0], data.iloc[-1, 0]
            interval = max(1, int((len(data) * 1e6) / ((end_freq - start_freq) * density)))
            sampled_data.append(data.iloc[np.arange(0, len(data), interval)])
        return sampled_data