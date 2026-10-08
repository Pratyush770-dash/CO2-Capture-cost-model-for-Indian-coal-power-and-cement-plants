"""
thermo.py
Water vapour pressure, simplified MEA-CO2 vapour-liquid equilibrium, CO2 compression work.
"""
import math
import numpy as np

R = 8.314462618          # kJ/kmol/K or J/mol/K
MW_CO2 = 44.01
MW_MEA = 61.08


def psat_water_kpa(T_K):
    """Antoine equation for water, two ranges (<100 C and 100-374 C), result in kPa."""
    T_C = T_K - 273.15
    if T_C < 100.0:
        A, B, C = 8.07131, 1730.63, 233.426
    else:
        A, B, C = 8.14019, 1810.94, 244.485
    mmhg = 10.0 ** (A - B / (C + T_C))
    return mmhg * 0.133322


class MEAVLE:
    """
    Simplified carbamate-type equilibrium for 30 wt% MEA:
        ln P*(kPa) = A + B/T + n * ln( alpha / (1 - 2*alpha) )
    B = -dH_abs/R, A fixed by an anchor point (see config.py).
    Valid for alpha < 0.5 and 300-400 K.
    """

    def __init__(self, sol):
        self.B = -sol["dH_abs_kj_mol"] * 1000.0 / R
        self.n = sol["vle_n"]
        a = sol["vle_anchor_alpha"]
        x = a / (1.0 - 2.0 * a)
        self.A = (math.log(sol["vle_anchor_p_kpa"])
                  - self.B / sol["vle_anchor_T_K"]
                  - self.n * math.log(x))

    def p_co2(self, alpha, T_K):
        alpha = np.asarray(alpha, dtype=float)
        x = alpha / (1.0 - 2.0 * alpha)
        return np.exp(self.A + self.B / T_K + self.n * np.log(x))

    def alpha_eq(self, p_kpa, T_K):
        lnx = (math.log(p_kpa) - self.A - self.B / T_K) / self.n
        x = math.exp(lnx)
        return x / (1.0 + 2.0 * x)


def compression_kwh_per_t(c):
    """Multi-stage CO2 compression with intercooling. Returns kWh per tonne CO2."""
    r_total = c["p_out_kpa"] / c["p_in_kpa"]
    r = r_total ** (1.0 / c["stages"])
    g = c["gamma"]
    w_kj_kg = (c["stages"] * g / (g - 1.0) * R * c["T_in_K"] / MW_CO2
               * (r ** ((g - 1.0) / g) - 1.0))
    w_kj_kg = w_kj_kg / c["eta"] * c["real_gas_factor"]
    return w_kj_kg / 3600.0 * 1000.0


def trapezoid(y, x):
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    return float(np.sum((y[1:] + y[:-1]) * (x[1:] - x[:-1]) * 0.5))
