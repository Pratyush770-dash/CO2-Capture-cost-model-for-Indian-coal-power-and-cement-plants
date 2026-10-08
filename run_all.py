"""
run_all.py
Runs the whole study: coal and cement base cases, comparison against
literature ranges, sensitivities, CSV/JSON/TXT outputs and figures.
Usage:  python run_all.py
"""
import json
import os
import pandas as pd

from config import default_params
from coal_plant import evaluate_coal
from cement_plant import evaluate_cement
import sensitivity as sens
import report

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")


def flag(value, lo, hi):
    return "inside literature range" if lo <= value <= hi else "outside literature range"


def main():
    os.makedirs(OUT, exist_ok=True)
    P = default_params()
    L = P["literature"]
    coal = evaluate_coal(P)
    cement = evaluate_cement(P)
    dc, dm = coal["design"], cement["design"]
    lines = []
    w = lines.append

    w("=" * 74)
    w("CO2 CAPTURE COST MODEL - INDIAN COAL POWER AND CEMENT (30 wt% MEA, 90% capture)")
    w("=" * 74)
    w("")
    w("A. SOLVENT AND ABSORBER DESIGN (coal case | cement case)")
    w("  Lean / rich loading (mol/mol):      %.3f / %.3f   |  %.3f / %.3f" %
      (dc["alpha_lean"], dc["alpha_rich"], dm["alpha_lean"], dm["alpha_rich"]))
    w("  Solvent circulation (kg/kg CO2):    %.1f          |  %.1f" %
      (dc["solvent_kg_per_kg_co2"], dm["solvent_kg_per_kg_co2"]))
    w("  Absorber packing height (m):        %.1f          |  %.1f" %
      (dc["absorber_height_m"], dm["absorber_height_m"]))
    w("  Absorber trains x diameter (m):     %d x %.1f       |  %d x %.1f" %
      (dc["absorber_trains"], dc["absorber_diameter_m"], dm["absorber_trains"], dm["absorber_diameter_m"]))
    w("")
    w("B. SOLVENT REGENERATION ENERGY (GJ per t CO2)")
    for k in ["desorption", "sensible", "stripping_steam"]:
        w("  %-18s %.2f          |  %.2f" % (k.replace("_", " "),
          dc["reboiler_split_gj_per_t"][k], dm["reboiler_split_gj_per_t"][k]))
    w("  %-18s %.2f          |  %.2f" % ("TOTAL reboiler", dc["reboiler_gj_per_t"], dm["reboiler_gj_per_t"]))
    w("  CO2 compression (kWh/t): %.0f" % dc["compression_kwh_per_t"])
    w("")
    w("C. COAL PLANT (660 MW supercritical unit, PLF %.0f%%)" % (P["coal_plant"]["plf"] * 100))
    w("  Net output: %.0f MW -> %.0f MW  (loss %.1f%%)" %
      (coal["net_mw_ref"], coal["net_mw_capture"], coal["net_output_loss_pct"]))
    w("    steam extraction %.0f MW, CO2 compression %.0f MW, auxiliaries %.0f MW" %
      (coal["penalty_steam_mw"], coal["penalty_compression_mw"], coal["penalty_aux_mw"]))
    w("  Net efficiency (GCV): %.1f%% -> %.1f%%  (penalty %.1f points)" %
      (coal["efficiency_ref_pct"], coal["efficiency_capture_pct"], coal["efficiency_penalty_pts"]))
    w("  CO2 captured: %.2f Mt/yr; emission intensity %.3f -> %.3f t/MWh" %
      (coal["co2_captured_mt_yr"], coal["emission_intensity_ref_t_mwh"], coal["emission_intensity_capture_t_mwh"]))
    w("  Capture capex: Rs %.0f crore (Rs %.0f per kW of reference net capacity)" %
      (coal["capex_capture_crore"], coal["capex_capture_inr_per_kw_ref"]))
    w("  Electricity cost (LCOE): Rs %.2f -> Rs %.2f per kWh  (+Rs %.2f, +%.0f%%)" %
      (coal["lcoe_ref_inr_kwh"], coal["lcoe_capture_inr_kwh"],
       coal["lcoe_increase_inr_kwh"], coal["lcoe_increase_pct"]))
    w("  Cost per tonne CO2 CAPTURED: Rs %.0f (USD %.1f)" % (coal["cost_captured_inr_t"], coal["cost_captured_usd_t"]))
    for k, v in coal["cost_captured_breakdown"].items():
        w("      %-24s Rs %.0f" % (k.replace("_", " "), v))
    w("  Cost per tonne CO2 AVOIDED:  Rs %.0f (USD %.1f)" % (coal["cost_avoided_inr_t"], coal["cost_avoided_usd_t"]))
    w("")
    w("D. CEMENT PLANT (%.2f Mt clinker/yr, %.2f Mt cement/yr)" % (cement["clinker_mt_yr"], cement["cement_mt_yr"]))
    w("  Kiln CO2: %.3f t/t clinker, %.2f Mt/yr; steam boiler adds %.2f Mt/yr (also captured)" %
      (cement["kiln_co2_t_per_t_clinker"], cement["kiln_co2_mt_yr"], cement["boiler_co2_mt_yr"]))
    w("  CO2 captured %.2f Mt/yr; net CO2 avoided %.2f Mt/yr (%.0f%% of kiln emission)" %
      (cement["co2_captured_mt_yr"], cement["co2_avoided_mt_yr"], cement["avoided_fraction_pct"]))
    w("  Steam boiler %.0f MWth; electricity %.1f MW (%.0f kWh/t CO2)" %
      (cement["boiler_heat_mw_th"], cement["electricity_mw"], cement["electricity_kwh_per_t_captured"]))
    w("  Capture capex: Rs %.0f crore" % cement["capex_capture_crore"])
    w("  Cost per tonne CO2 CAPTURED: Rs %.0f (USD %.1f)" % (cement["cost_captured_inr_t"], cement["cost_captured_usd_t"]))
    for k, v in cement["cost_captured_breakdown"].items():
        w("      %-24s Rs %.0f" % (k.replace("_", " "), v))
    w("  Cost per tonne CO2 AVOIDED:  Rs %.0f (USD %.1f)" % (cement["cost_avoided_inr_t"], cement["cost_avoided_usd_t"]))
    w("  Added cost: Rs %.0f per t clinker, Rs %.0f per t cement (Rs %.0f per 50 kg bag)" %
      (cement["added_cost_inr_per_t_clinker"], cement["added_cost_inr_per_t_cement"],
       cement["added_cost_inr_per_50kg_bag"]))
    w("")
    w("E. COMPARISON WITH LITERATURE RANGES")
    w("  Reboiler duty %.2f GJ/t vs %.1f-%.1f: %s" %
      (dc["reboiler_gj_per_t"], L["reboiler_gj_per_t_low"], L["reboiler_gj_per_t_high"],
       flag(dc["reboiler_gj_per_t"], L["reboiler_gj_per_t_low"], L["reboiler_gj_per_t_high"])))
    w("  Efficiency penalty %.1f pts vs %.0f-%.0f: %s" %
      (coal["efficiency_penalty_pts"], L["efficiency_penalty_pts_low"], L["efficiency_penalty_pts_high"],
       flag(coal["efficiency_penalty_pts"], L["efficiency_penalty_pts_low"], L["efficiency_penalty_pts_high"])))
    w("  Compression %.0f kWh/t vs %.0f-%.0f: %s" %
      (dc["compression_kwh_per_t"], L["compression_kwh_per_t_low"], L["compression_kwh_per_t_high"],
       flag(dc["compression_kwh_per_t"], L["compression_kwh_per_t_low"], L["compression_kwh_per_t_high"])))
    w("  Coal avoided cost USD %.0f/t vs typical global USD 60-90/t" % coal["cost_avoided_usd_t"])
    w("  Earlier Indian case studies (Energy Procedia 54) report +Rs %.1f-%.1f/kWh and Rs %.0f-%.0f/t avoided."
      % (L["india_coal_incr_coe_inr_kwh_low"], L["india_coal_incr_coe_inr_kwh_high"],
         L["india_coal_avoided_inr_t_low"], L["india_coal_avoided_inr_t_high"]))
    w("  Our Rs/kWh and Rs/t values are higher than those older figures. Some of the gap is")
    w("  probably cost escalation since then, but that study's inputs are not reproduced here,")
    w("  so treat the gap as unexplained and compare in USD terms (global range above).")
    w("")
    w("F. KEY ASSUMPTIONS (edit in config.py)")
    w("  WACC %.0f%%, life %d yr, coal Rs %.0f/t, GCV %.0f kcal/kg, USD/INR %.0f" %
      (P["finance"]["wacc"] * 100, P["finance"]["capture_life_yr"], P["coal_plant"]["coal_price_inr_t"],
       P["coal_plant"]["coal_gcv_kcal_kg"], P["macro"]["usd_inr"]))
    w("  Capex island ref USD %.0f M at %.0f t/h, location factor %.2f, TCI factor %.2f" %
      (P["capex"]["island_ref_usd_2020"] / 1e6, P["capex"]["island_ref_t_h"],
       P["capex"]["loc_island"], P["capex"]["tci_factor"]))
    w("  Transport and storage of CO2 are NOT included (capture + compression only).")
    w("  Capex is scaled from literature reference costs, so it is the largest uncertainty;")
    w("  see the tornado charts. The absorber model is a short-cut with a lumped KGa, not")
    w("  the calibrated rate-based model.")

    text = "\n".join(lines)
    print(text)
    with open(os.path.join(OUT, "report.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)

    # ---------------- sensitivities ----------------
    base_coal, tor_coal = sens.tornado("coal")
    base_cem, tor_cem = sens.tornado("cement")
    lean_df = sens.lean_loading_sweep("coal")
    rate_df = sens.capture_rate_sweep("coal")
    price_df = sens.coal_price_sweep()
    tor_coal.to_csv(os.path.join(OUT, "tornado_coal.csv"), index=False)
    tor_cem.to_csv(os.path.join(OUT, "tornado_cement.csv"), index=False)
    lean_df.to_csv(os.path.join(OUT, "sweep_lean_loading_coal.csv"), index=False)
    rate_df.to_csv(os.path.join(OUT, "sweep_capture_rate_coal.csv"), index=False)
    price_df.to_csv(os.path.join(OUT, "sweep_coal_price.csv"), index=False)

    print("\nG. SENSITIVITY (coal, cost of CO2 avoided, Rs/t)")
    print(tor_coal[["parameter", "avoided_low", "avoided_high"]].round(0).to_string(index=False))
    print("\nH. SENSITIVITY (cement, cost of CO2 avoided, Rs/t)")
    print(tor_cem[["parameter", "avoided_low", "avoided_high"]].round(0).to_string(index=False))
    print("\nI. COAL PRICE vs ELECTRICITY COST INCREASE")
    print(price_df[["value", "lcoe_increase_inr_kwh", "cost_avoided_inr_t"]].round(2).to_string(index=False))

    # ---------------- save results ----------------
    summary = pd.DataFrame([
        {"case": "coal", "reboiler_gj_per_t": dc["reboiler_gj_per_t"],
         "cost_captured_inr_t": coal["cost_captured_inr_t"], "cost_avoided_inr_t": coal["cost_avoided_inr_t"],
         "cost_captured_usd_t": coal["cost_captured_usd_t"], "cost_avoided_usd_t": coal["cost_avoided_usd_t"],
         "lcoe_increase_inr_kwh": coal["lcoe_increase_inr_kwh"]},
        {"case": "cement", "reboiler_gj_per_t": dm["reboiler_gj_per_t"],
         "cost_captured_inr_t": cement["cost_captured_inr_t"], "cost_avoided_inr_t": cement["cost_avoided_inr_t"],
         "cost_captured_usd_t": cement["cost_captured_usd_t"], "cost_avoided_usd_t": cement["cost_avoided_usd_t"],
         "lcoe_increase_inr_kwh": float("nan")},
    ])
    summary.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as fh:
        json.dump({"coal": coal, "cement": cement, "parameters": P}, fh, indent=2, default=float)

    report.make_all(coal, cement, tor_coal, tor_cem, lean_df, rate_df, price_df, OUT)
    print("\nDone. Results and figures saved in: %s" % OUT)


if __name__ == "__main__":
    main()
