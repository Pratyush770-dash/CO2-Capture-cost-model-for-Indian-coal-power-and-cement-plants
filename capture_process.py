"""
capture_process.py
Short-cut MEA absorber/stripper model. Gives:
  - rich loading, solvent circulation
  - reboiler duty split into desorption, sensible and stripping-steam terms
  - absorber packing height and diameter
  - auxiliary electricity (blower, pumps, cooling water, CO2 compression)
"""
import math
import numpy as np
from thermo import (MEAVLE, MW_CO2, MW_MEA, R, psat_water_kpa,
                    compression_kwh_per_t, trapezoid)


def design_capture(co2_in_t_h, y_co2, capture_rate, alpha_lean, P):
    s = P["solvent"]
    p = P["process"]
    vle = MEAVLE(s)

    # ---------------- gas side balances (kmol/h) ----------------
    n_co2_in = co2_in_t_h * 1000.0 / MW_CO2
    n_gas = n_co2_in / y_co2
    n_inert = n_gas - n_co2_in
    n_cap = capture_rate * n_co2_in
    captured_t_h = n_cap * MW_CO2 / 1000.0

    # ---------------- loadings ----------------
    p_co2_bottom = y_co2 * p["P_abs_kpa"]
    a_eq = vle.alpha_eq(p_co2_bottom, p["T_abs_K"])
    a_rich = alpha_lean + p["rich_approach"] * (a_eq - alpha_lean)
    d_alpha = a_rich - alpha_lean
    if a_rich >= 0.5 or d_alpha <= 0.02:
        raise ValueError("Loadings not feasible: lean=%.3f rich=%.3f" % (alpha_lean, a_rich))

    # Lean loading must be reachable at reboiler conditions
    p_co2_reb = p["P_reb_kpa"] - s["x_water"] * psat_water_kpa(p["T_reb_K"])
    a_min = vle.alpha_eq(p_co2_reb, p["T_reb_K"])
    if alpha_lean < a_min + 0.005:
        raise ValueError("Lean loading %.3f below reboiler limit %.3f" % (alpha_lean, a_min))

    # ---------------- solvent circulation ----------------
    c_mea = s["mea_wt_frac"] * 1000.0 / MW_MEA            # mol MEA per kg solution
    kg_per_kmol_co2 = 1000.0 / (c_mea * d_alpha)           # kg solvent per kmol CO2 captured
    solvent_kg_h = kg_per_kmol_co2 * n_cap
    solvent_m3_s = solvent_kg_h / s["density_kg_m3"] / 3600.0
    n_mea = solvent_kg_h * c_mea / 1000.0                  # kmol MEA / h

    # ---------------- reboiler duty (kJ per mol CO2) ----------------
    q_des = s["dH_abs_kj_mol"]
    T_rich_in = p["T_reb_K"] - p["dT_cross_K"]
    q_sens = (kg_per_kmol_co2 / 1000.0) * s["cp_kj_kg_k"] * (p["T_reb_K"] - T_rich_in)
    p_h2o_top = s["x_water"] * psat_water_kpa(p["T_top_K"])
    ratio_top = p_h2o_top / (p["P_top_kpa"] - p_h2o_top)    # mol H2O per mol CO2 overhead
    q_strip = ratio_top * p["dh_vap_kj_mol"]
    q_total = q_des + q_sens + q_strip
    gj_per_t = {"desorption": q_des / MW_CO2,
                "sensible": q_sens / MW_CO2,
                "stripping_steam": q_strip / MW_CO2}
    reb_gj_per_t = q_total / MW_CO2
    q_reb_mw = reb_gj_per_t * captured_t_h / 3.6

    # ---------------- absorber sizing ----------------
    T = p["T_abs_K"]
    V_m3_s = n_gas / 3600.0 * R * T / p["P_abs_kpa"]
    area = V_m3_s / p["gas_velocity_m_s"]
    a_max = math.pi / 4.0 * p["d_max_m"] ** 2
    n_trains = max(1, math.ceil(area / a_max))
    diameter = math.sqrt(4.0 * area / (math.pi * n_trains))
    g_flux = (n_inert / 3600.0) / area                      # kmol inert / m2 / s

    Y_in = y_co2 / (1.0 - y_co2)
    Y_out = Y_in * (1.0 - capture_rate)
    Y = np.linspace(Y_out, Y_in, 801)
    alpha_Y = alpha_lean + (n_inert / n_mea) * (Y - Y_out)
    y_loc = Y / (1.0 + Y)
    p_loc = y_loc * p["P_abs_kpa"]
    p_star = vle.p_co2(alpha_Y, T)
    drive = p_loc - p_star
    if np.min(drive) <= 0.0:
        raise ValueError("Negative driving force in absorber: raise rich_approach margin "
                         "or lower capture rate / lean loading")
    height = trapezoid(g_flux / (p["kga_eff"] * drive), Y)

    # ---------------- electricity (MW) ----------------
    blower_kw = V_m3_s * p["dp_blower_kpa"] / p["eta_blower"]
    pump_kw = solvent_m3_s * p["pump_head_kpa"] / p["eta_pump"]
    comp_kwh_t = compression_kwh_per_t(P["compression"])
    comp_kw = comp_kwh_t * captured_t_h
    # cooling water pumping
    condenser_kw = ratio_top * n_cap * 1000.0 / 3600.0 * p["dh_vap_kj_mol"]
    lean_cooler_kw = (solvent_kg_h / 3600.0) * s["cp_kj_kg_k"] * (T + p["dT_cross_K"] - 313.15)
    comp_heat_kw = comp_kw * P["compression"]["heat_rejected_frac"]
    cw_load_kw = condenser_kw + lean_cooler_kw + comp_heat_kw
    cw_m3_s = cw_load_kw / (p["cw_cp_kj_kg_k"] * p["cw_dT_K"] * 1000.0)
    cw_kw = cw_m3_s * p["cw_head_kpa"] / p["eta_pump"]

    return {
        "captured_t_h": captured_t_h,
        "co2_in_t_h": co2_in_t_h,
        "y_co2": y_co2,
        "alpha_lean": alpha_lean,
        "alpha_rich": a_rich,
        "alpha_eq_bottom": a_eq,
        "alpha_min_reboiler": a_min,
        "solvent_kg_per_kg_co2": kg_per_kmol_co2 / MW_CO2,
        "solvent_m3_h": solvent_m3_s * 3600.0,
        "reboiler_gj_per_t": reb_gj_per_t,
        "reboiler_split_gj_per_t": gj_per_t,
        "steam_ratio_top": ratio_top,
        "q_reb_mw": q_reb_mw,
        "absorber_height_m": height,
        "absorber_diameter_m": diameter,
        "absorber_trains": n_trains,
        "gas_flow_m3_s": V_m3_s,
        "blower_mw": blower_kw / 1000.0,
        "pumps_mw": pump_kw / 1000.0,
        "cooling_water_mw": cw_kw / 1000.0,
        "compression_mw": comp_kw / 1000.0,
        "compression_kwh_per_t": comp_kwh_t,
        "aux_mw": (blower_kw + pump_kw + cw_kw) / 1000.0,
    }
