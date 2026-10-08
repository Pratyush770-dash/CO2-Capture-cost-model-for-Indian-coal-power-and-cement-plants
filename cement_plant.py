"""
cement_plant.py
Indian integrated cement plant (kiln flue gas) with MEA capture.
Steam comes from a dedicated coal boiler whose flue gas is also captured
(solved by fixed-point iteration). Electricity comes from the grid.
"""
from capture_process import design_capture
from economics import (crf, island_capex_inr, compression_capex_inr,
                       boiler_capex_inr, consumables_inr_per_yr)


def evaluate_cement(P):
    c = P["cement_plant"]
    f = P["finance"]
    cap = P["capex"]

    # ---------------- base plant ----------------
    hours = c["kiln_days"] * 24.0
    clinker_t_yr = c["clinker_tpd"] * c["kiln_days"]
    cement_t_yr = clinker_t_yr / c["clinker_factor"]
    fuel_co2_per_t_clk = c["thermal_gj_per_t_clk"] * c["kiln_fuel_ef_kg_gj"] / 1000.0
    kiln_co2_per_t_clk = c["process_co2_t_per_t_clk"] + fuel_co2_per_t_clk
    kiln_co2_t_h = clinker_t_yr * kiln_co2_per_t_clk / hours

    # ---------------- iterate: boiler CO2 joins the captured stream ----------------
    boiler_co2_t_h = 0.0
    for _ in range(60):
        co2_total = kiln_co2_t_h + boiler_co2_t_h
        n1 = kiln_co2_t_h / c["y_co2"]
        n2 = boiler_co2_t_h / c["boiler_y_co2"] if boiler_co2_t_h > 0 else 0.0
        y_mix = co2_total / (n1 + n2) if (n1 + n2) > 0 else c["y_co2"]
        d = design_capture(co2_total, y_mix, c["capture_rate"], c["alpha_lean"], P)
        boiler_fuel_gj_h = d["q_reb_mw"] * 3.6 / c["boiler_eff"]
        new_boiler = boiler_fuel_gj_h * c["boiler_ef_kg_gj"] / 1000.0
        if abs(new_boiler - boiler_co2_t_h) < 1e-6:
            boiler_co2_t_h = new_boiler
            break
        boiler_co2_t_h = new_boiler
    co2_total = kiln_co2_t_h + boiler_co2_t_h
    boiler_fuel_gj_h = d["q_reb_mw"] * 3.6 / c["boiler_eff"]

    # ---------------- annual quantities ----------------
    captured_t_yr = d["captured_t_h"] * hours
    elec_mw = d["compression_mw"] + d["aux_mw"]
    elec_mwh_yr = elec_mw * hours
    r = crf(f["wacc"], f["capture_life_yr"])

    # ---------------- capex ----------------
    capex_island = island_capex_inr(P, d["captured_t_h"], y_mix)
    capex_comp = compression_capex_inr(P, d["compression_mw"] * 1000.0)
    capex_boiler = boiler_capex_inr(P, d["q_reb_mw"] / c["boiler_eff"])
    tci = (capex_island + capex_comp + capex_boiler) * cap["tci_factor"]

    # ---------------- annual costs ----------------
    capex_ann = r * tci
    fom = cap["fom_frac"] * tci
    consum = consumables_inr_per_yr(P, captured_t_yr)
    elec_cost = elec_mwh_yr * 1000.0 * c["elec_price_inr_kwh"]
    boiler_cost = boiler_fuel_gj_h * hours * c["boiler_fuel_price_inr_gj"]
    total_cost = capex_ann + fom + consum + elec_cost + boiler_cost
    cost_captured = total_cost / captured_t_yr

    # ---------------- emissions ----------------
    base_t_yr = kiln_co2_t_h * hours
    stack_t_yr = (1.0 - c["capture_rate"]) * co2_total * hours
    indirect_t_yr = elec_mwh_yr * c["grid_ef_t_mwh"]
    net_t_yr = stack_t_yr + indirect_t_yr
    avoided_t_yr = base_t_yr - net_t_yr
    cost_avoided = total_cost / avoided_t_yr

    breakdown = {
        "capex": capex_ann / captured_t_yr,
        "fixed_om": fom / captured_t_yr,
        "solvent_and_chemicals": consum / captured_t_yr,
        "electricity": elec_cost / captured_t_yr,
        "steam_fuel": boiler_cost / captured_t_yr,
    }
    return {
        "case": "Cement plant (kiln flue gas)",
        "clinker_mt_yr": clinker_t_yr / 1e6,
        "cement_mt_yr": cement_t_yr / 1e6,
        "kiln_co2_t_per_t_clinker": kiln_co2_per_t_clk,
        "kiln_co2_mt_yr": base_t_yr / 1e6,
        "boiler_co2_mt_yr": boiler_co2_t_h * hours / 1e6,
        "co2_captured_mt_yr": captured_t_yr / 1e6,
        "co2_avoided_mt_yr": avoided_t_yr / 1e6,
        "avoided_fraction_pct": avoided_t_yr / base_t_yr * 100.0,
        "y_co2_mixed": y_mix,
        "reboiler_gj_per_t": d["reboiler_gj_per_t"],
        "boiler_heat_mw_th": d["q_reb_mw"] / c["boiler_eff"],
        "electricity_mw": elec_mw,
        "electricity_kwh_per_t_captured": elec_mw * 1000.0 / d["captured_t_h"],
        "capex_capture_crore": tci / 1e7,
        "cost_captured_inr_t": cost_captured,
        "cost_captured_breakdown": breakdown,
        "cost_avoided_inr_t": cost_avoided,
        "cost_captured_usd_t": cost_captured / P["macro"]["usd_inr"],
        "cost_avoided_usd_t": cost_avoided / P["macro"]["usd_inr"],
        "added_cost_inr_per_t_clinker": total_cost / clinker_t_yr,
        "added_cost_inr_per_t_cement": total_cost / cement_t_yr,
        "added_cost_inr_per_50kg_bag": total_cost / cement_t_yr * 0.05,
        "design": d,
    }
