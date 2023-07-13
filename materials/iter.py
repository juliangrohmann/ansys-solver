def eval_limits(yield_strength, ult_strength, uniform_elongation, elastic_mod):
    s_m_val = s_m(ult_strength, yield_strength)
    s_e_val = s_e(ult_strength, uniform_elongation, elastic_mod)

    mem_stress_lim = max(
        s_m_val,  # 3121.1.1.2a (immediate plastic collapse/instability)
        s_e_val,  # 3121.2.1.1 (immediate plastic flow localization)
        min(1.5 * s_m_val, yield_strength))  # 3121.1.1.3 (immediate plastic collapse/instability)
    lin_stress_lim = k_eff() * s_m_val  # 3121.1.1.2a (immediate plastic collapse/instability)

    return {
        'membrane_stress': mem_stress_lim,
        'linearized_stress': lin_stress_lim
    }


def s_m(s_u, s_y):
    return min(1/2.7 * s_u, 2/3 * s_y)


def s_e(s_u, e_u, E, r_1=1.0):
    return 1/3 * (s_u + 0.5 * E * (e_u - 0.02) / r_1)


def k_eff():
    return 1.27