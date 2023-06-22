from scipy.stats import qmc
import pandas as pd


class PropertySampler:
    def __init__(self):
        self.props = {}

    def add_property(self, name, min_val, max_val):
        self.props[name] = (min_val, max_val)

    def random(self, n):
        sampler = qmc.LatinHypercube(d=len(self.props.keys()))
        raw_samples = sampler.random(n=n)
        df = pd.DataFrame(raw_samples, columns=list(self.props.keys()))

        for prop in df.columns.tolist():
            min_val = self.props[prop][0]
            max_val = self.props[prop][1]
            df[prop] = min_val + df[prop] * (max_val - min_val)

        return df
