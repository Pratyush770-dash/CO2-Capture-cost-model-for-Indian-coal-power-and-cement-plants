"""
coal_plant.py
Indian supercritical coal unit with and without MEA capture.
Outputs: energy penalty, cost per tonne CO2 captured and avoided, LCOE change.
"""
from capture_process import design_capture
from economics import (crf, island_capex_inr, compression_capex_inr,
                       consumables_inr_per_yr)

KCAL_TO_KJ = 4.1868


def evaluate_coal(P):
    c = P["coal_plant"]
    f = P["finance"]
    cap = P["capex"]

    # ---------------- base plant ----------------
    heat_in_mw = c["net_mw"] * c["heat_rate_kcal_kwh"] * KCAL_TO_KJ / 3600.0
    gcv_mj_kg = c["coal_gcv_kcal_kg"] * KCAL_TO_KJ / 1000.0
    ef_kg_mj = c["coal_c_frac"] * 44.01 / 12.011 / gcv_mj_kg
    co2_t_h = heat_in_mw * 3600.0 * ef_kg_mj / 1000.0
    coal_t_h = heat_in_mw * 3600.0 / gcv_mj_kg / 1000.0
    eff_ref = c["net_mw"] / heat_in_mw

    # ---------------- capture design ----------------
    d = design_capture(co2_t_h, c["y_co2"], c["capture_rate"], c["alpha_lean"], P)

    # ---------------- energy penalty ----------------
    T_steam = P["process"]["T_reb_K"] + c["dT_steam_K"]
    steam_factor = c["turbine_eta"] * (1.0 - c["T_cond_K"] / T_steam)   # MWe lost per MWth
    w_steam = d["q_reb_mw"] * steam_factor
    w_comp = d["compression_mw"]
    w_aux = d["aux_mw"]
    w_total = w_steam + w_comp + w_aux
    net_cap = c["net_mw"] - w_total
    eff_cap = net_cap / heat_in_mw

    # ---------------- annual quantities ----------------
    hours = 8760.0 * c["plf"]
    mwh_ref = c["net_mw"] * hours
    mwh_cap = net_cap * hours
    captured_t_yr = d["captured_t_h"] * hours
    r = crf(f["wacc"], f["capture_life_yr"])

    # ---------------- capex ----------------
    capex_island = island_capex_inr(P, d["captured_t_h"], c["y_co2"])
    capex_comp = compression_capex_inr(P, d["compression_mw"] * 1000.0)
    tci_cap = (capex_island + capex_comp) * cap["tci_factor"]
    base_capex = c["base_capex_inr_per_kw"] * c["net_mw"] * 1000.0

    # ---------------- annual costs (INR/yr) ----------------
    fom_base = c["base_fom_frac"] * base_capex
    fuel = coal_t_h * hours * c["coal_price_inr_t"]
    vom_base = c["base_vom_inr_kwh"] * mwh_ref * 1000.0
    fom_cap = cap["fom_frac"] * tci_cap
    consum = consumables_inr_per_yr(P, captured_t_yr)

    lcoe_ref = (r * base_capex + fom_base + fuel + vom_base) / (mwh_ref * 1000.0)
    lcoe_cap = (r * (base_capex + tci_cap) + fom_base + fom_cap + fuel + vom_base + consum) \
        / (mwh_cap * 1000.0)

    # ---------------- CO2 metrics ----------------
    e_ref = co2_t_h / c["net_mw"]                                  # t/MWh
    e_cap = co2_t_h * (1.0 - c["capture_rate"]) / net_cap
    avoided_cost = (lcoe_cap - lcoe_ref) * 1000.0 / (e_ref - e_cap)  # INR / t avoided

    # cost per tonne captured: energy penalty valued at the plant's marginal generation cost
    marginal_inr_mwh = (fuel + vom_base) / mwh_ref
    energy_penalty_cost = (mwh_ref - mwh_cap) * marginal_inr_mwh
    capex_ann = r * tci_cap
    cost_captured = (capex_ann + fom_cap + consum + energy_penalty_cost) / captured_t_yr
    breakdown = {
        "capex": capex_ann / captured_t_yr,
        "fixed_om": fom_cap / captured_t_yr,
        "solvent_and_chemicals": consum / captured_t_yr,
        "energy_penalty": energy_penalty_cost / captured_t_yr,
    }

    return {
        "case": "Coal supercritical unit",
        "net_mw_ref": c["net_mw"],
        "net_mw_capture": net_cap,
        "efficiency_ref_pct": eff_ref * 100.0,
        "efficiency_capture_pct": eff_cap * 100.0,
        "efficiency_penalty_pts": (eff_ref - eff_cap) * 100.0,
        "net_output_loss_pct": w_total / c["net_mw"] * 100.0,
        "penalty_steam_mw": w_steam,
        "penalty_compression_mw": w_comp,
        "penalty_aux_mw": w_aux,
        "steam_factor_mwe_per_mwth": steam_factor,
        "co2_emitted_t_h": co2_t_h,
        "co2_captured_mt_yr": captured_t_yr / 1e6,
        "emission_intensity_ref_t_mwh": e_ref,
        "emission_intensity_capture_t_mwh": e_cap,
        "capex_capture_crore": tci_cap / 1e7,
        "capex_capture_inr_per_kw_ref": tci_cap / (c["net_mw"] * 1000.0),
        "lcoe_ref_inr_kwh": lcoe_ref,
        "lcoe_capture_inr_kwh": lcoe_cap,
        "lcoe_increase_inr_kwh": lcoe_cap - lcoe_ref,
        "lcoe_increase_pct": (lcoe_cap / lcoe_ref - 1.0) * 100.0,
        "cost_captured_inr_t": cost_captured,
        "cost_captured_breakdown": breakdown,
        "cost_avoided_inr_t": avoided_cost,
        "cost_captured_usd_t": cost_captured / P["macro"]["usd_inr"],
        "cost_avoided_usd_t": avoided_cost / P["macro"]["usd_inr"],
        "design": d,
    }
