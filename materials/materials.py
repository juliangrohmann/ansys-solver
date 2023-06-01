import abc
import math

import matplotlib.pyplot as plt
import numpy as np

from materials.matprops import MatProps


TEMPS = [22, 80, 180, 320, 450, 550, 660, 760, 870]


class Material:
    def __init__(self):
        self.temperature_props = {}

    def plot_bilinear(self, t, **kwargs):
        if t not in self.temperature_props:
            print(f"Invalid temperature in plot_bilinear! t = {t}")
            return

        mat_props = self.temperature_props[t]
        x = [0, mat_props.yield_strain, mat_props.ult_strain]
        y = [0, mat_props.yield_strength / 1e6, mat_props.ult_strength / 1e6]

        plt.plot(x, y, **kwargs, zorder=2)
        return x, y

    @abc.abstractmethod
    def get_name(self):
        pass


class W3Re(Material):
    def __init__(self):
        super().__init__()

        self.temperature_props = {
            100: MatProps(2.21e10, 8.40e8, 9.34e8, 8.237),
            200: MatProps(2.21e10, 7.31e8, 8.74e8, 14.14),
            300: MatProps(2.21e10, 7.06e8, 8.25e8, 18.11),
            600: MatProps(-1, -1, 5.96e8, 17.29),
            1100: MatProps(-1, -1, 4.08e8, 10.65),
            1300: MatProps(-1, -1, 4.35e8, 23.62),
        }

    def get_name(self):
        return "Tungsten Alloy W-3%Re"

    def __str__(self):
        return "w_3re"


class CoefficientMaterial(Material):
    def __init__(self, youngs_base, yield_base, ult_strength_base, ult_strain_base):
        super().__init__()

        self.temperature_props = {}

        youngs_moduli = [_prop_from_coeffs(youngs_base, _youngs_mod_coeffs(t), t) for t in TEMPS]
        yield_strengths = [_prop_from_coeffs(yield_base, _yield_coeffs(t), t) for t in TEMPS]
        ult_strengths = [_prop_from_coeffs(ult_strength_base, self._ult_strength_coeffs(t), t) for t in TEMPS]
        ult_strains = [_prop_from_coeffs(ult_strain_base, self._ult_strain_coeffs(t), t) for t in TEMPS]

        for i in range(len(TEMPS)):
            self.temperature_props[TEMPS[i]] = MatProps(youngs_moduli[i], yield_strengths[i], ult_strengths[i], ult_strains[i])

    def plot_stress_strain(self, t, res, axis=None, **kwargs):
        if t not in self.temperature_props:
            print(f"Invalid temperature in plot_stress_strain! t = {t}")
            return None

        x, y = self.get_stress_strain(t, res)

        if not axis:
            axis = plt.subplot()

        axis.plot(x, y, **kwargs)
        return axis

    def get_stress_strain(self, t, res):
        if t not in self.temperature_props:
            print(f"Invalid temperature in get_stress_strain! t = {t}")
            return None

        mat_props = self.temperature_props[t]
        y = np.linspace(0, mat_props.ult_strength, res)
        x = [self.get_strain(stress, t) for stress in y]

        y = [val / 1e6 for val in y]

        return x, y

    def get_strain(self, stress, t):
        if t not in self.temperature_props:
            print(f"Invalid temperature in get_strain! t = {t}")
            return None

        mat_props = self.temperature_props[t]
        if stress <= mat_props.yield_strength:
            strain = (stress / mat_props.youngs_mod + 0.002 * (stress / mat_props.yield_strength) ** _get_n_t(t)) * 100
        else:
            term_1 = (stress - mat_props.yield_strength) / _get_E_y_t(mat_props.youngs_mod, _get_n_t(t), mat_props.yield_strength)
            term_2 = (mat_props.ult_strain / 100) * \
                ((stress - mat_props.yield_strength) / (mat_props.ult_strength - mat_props.yield_strength)) ** self._get_m_t(t)
            strain = (term_1 + term_2) * 100 + self.get_strain(mat_props.yield_strength, t)

        return strain

    @abc.abstractmethod
    def _ult_strength_coeffs(self, t):
        pass

    @abc.abstractmethod
    def _ult_strain_coeffs(self, t):
        pass

    @abc.abstractmethod
    def _get_m_t(self, t):
        pass


class Duplex(CoefficientMaterial):
    def __init__(self):
        super().__init__(
            2.27E11,
            7.31E8,
            8.7E8,
            15.8
            # [1.000, 0.943, 0.834, 0.758, 0.728, 0.683, 0.528, 0.354, 0.170, 0.031]
        )

    def get_name(self):
        return "Stainless Steel E 1.4462 (Duplex)"

    def _ult_strength_coeffs(self, t):
        if 22 <= t < 450:
            return 0.85, 450, 9.6E13, 5
        elif 450 <= t < 660:
            return 0.85, 450, 1.3E5, 2
        elif 660 <= t <= 960:
            return 0.51, 660, 200, 0.8
        else:
            print(f"Invalid duplex temperature! t = {t}")

    def _ult_strain_coeffs(self, t):
        if 22 <= t < 450:
            return 0.85, 450, 9.6E13, 5
        elif 450 <= t < 660:
            return 0.85, 450, 1.3E5, 2
        elif 660 <= t <= 960:
            return 0.51, 660, 200, 0.8
        else:
            print(f"Invalid duplex temperature! t = {t}")

    def _get_m_t(self, t):
        return 5.6 - t / 200

    def __str__(self):
        return "duplex"


class AISI304(CoefficientMaterial):
    def __init__(self):
        super().__init__(
            1.87E11,
            3.98E8,
            7.09E8,
            60.6
            # [1.000, 0.839, 0.764, 0.698, 0.678, 0.595, 0.523, 0.357, 0.181, 0.116]
        )

    def get_name(self):
        return "Stainless Steel E 1.4301 (AISI 304)"

    def _ult_strength_coeffs(self, t):
        if 22 <= t < 450:
            return 0.7, 450, 4.8E13, 5
        elif 450 <= t < 660:
            return 0.7, 450, 1.92E5, 2
        elif 660 <= t <= 960:
            return 0.06, 960, -2.2E5, 2
        else:
            print(f"Invalid AISI 304 temperature! t = {t}")

    def _ult_strain_coeffs(self, t):
        if 22 <= t < 450:
            return 0.7, 450, 4.8E13, 5
        elif 450 <= t < 660:
            return 0.7, 450, 1.92E5, 2
        elif 660 <= t <= 960:
            return 0.06, 960, -2.2E5, 2
        else:
            print(f"Invalid AISI 304 temperature! t = {t}")

    def _get_m_t(self, t):
        return 2.3 - t / 1000

    def __str__(self):
        return "aisi_304"


def eng_to_true_stress(eng_stress, eng_strain):
    return eng_stress * (1 + eng_strain / 100)


def eng_to_true_strain(eng_strain):
    return math.log(1 + eng_strain / 100) * 100


def _prop_from_coeffs(base, coeffs, t):
    factor = coeffs[0] - ((t - coeffs[1]) ** coeffs[3]) / coeffs[2]
    return base * factor


def _yield_coeffs(t):
    if 22 <= t < 300:
        return 1.0, 22, 45, 0.5
    elif 300 <= t < 850:
        return 0.63, 300, 5.7E5, 2
    elif 850 <= t < 1000:
        return 0.1, 850, 600, 0.8
    else:
        print(f"Invalid yield coeff temperature! t = {t}")


def _youngs_mod_coeffs(t):
    if 22 <= t < 922:
        return 1.0, 22, 900, 1
    else:
        print(f"Invalid AISI 304 temperature! t = {t}")


def _get_E_y_t(youngs_modulus, n_t, yield_strength):
    return youngs_modulus / (1 + 0.002 * n_t * (youngs_modulus / yield_strength))


def _get_n_t(t):
    return 6 + 0.2 * (t ** 0.5)
