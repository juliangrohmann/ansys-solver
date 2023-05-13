import numpy as np
import matplotlib.pyplot as plt


class MultilinearModel:
    def __init__(self, mat, n):
        self.mat = mat
        self.temp_table = {}
        self.n = n

        for t in mat.temperature_props:
            mat_props = mat.temperature_props[t]
            pts = [Keypoint(0, 0)]
            stresses = np.linspace(mat_props.yield_strength, mat_props.ult_strength, n)
            pts = pts + [Keypoint(stress, mat.get_strain(stress, t)) for stress in stresses]
            rate = (pts[-1].stress - pts[-2].stress) / (pts[-1].strain - pts[-2].strain)
            pts.append(Keypoint((100 - pts[-1].strain) * rate + pts[-1].stress, 100))
            self.temp_table[t] = pts

    def plot(self, t, axis=None, **kwargs):
        if not axis:
            axis = plt.subplot()

        x = [pt.strain for pt in self.temp_table[t][:-1]]
        y = [pt.stress / 1e6 for pt in self.temp_table[t][:-1]]

        axis.plot(x, y, **kwargs)
        axis.scatter(x, y)
        return axis

    def print_keypoints(self, t, absolute=True):
        for pt in self.temp_table[t]:
            strain = pt.strain if absolute else get_plastic_strain(pt.stress, pt.strain, self.mat.temperature_props[t].youngs_mod)
            strain_label = "Abs Strain" if absolute else "Plastic Strain"
            print(f"Stress: {pt.stress:.2e},\t {strain_label}: {strain:.2e}")

    def get_temps(self):
        return sorted(list(self.temp_table.keys()))


class Keypoint:
    def __init__(self, stress, strain):
        self.stress = stress
        self.strain = strain


def get_plastic_strain(stress, strain, elastic_mod):
    elastic_strain = (stress / elastic_mod) + 0.002
    return max(strain / 100 - elastic_strain, 0)
