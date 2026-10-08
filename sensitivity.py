"""
sensitivity.py
One-at-a-time sensitivity (tornado) and parameter sweeps for both cases.
"""
import pandas as pd
from config import default_params
from coal_plant import evaluate_coal
from cement_plant import evaluate_cement


def set_param(P, path, value):
    d = P
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = value


def _run(case, path, value):
    P = default_params()
    set_param(P, path, value)
    try:
        return evaluate_coal(P) if case == "coal" else evaluate_cement(P)
    except ValueError:
        return None


COAL_CASES = [
    ("Coal price (Rs/t: 3500 / 7000)", ("coal_plant", "coal_price_inr_t"), 3500.0, 7000.0),
    ("Plant load factor (0.65 / 0.90)", ("coal_plant", "plf"), 0.65, 0.90),
    ("WACC (8% / 12%)", ("finance", "wacc"), 0.08, 0.12),
    ("Capture rate (80% / 95%)", ("coal_plant", "capture_rate"), 0.80, 0.95),
    ("Lean loading (0.20 / 0.28)", ("coal_plant", "alpha_lean"), 0.20, 0.28),
    ("Capex location factor (0.35 / 0.70)", ("capex", "loc_island"), 0.35, 0.70),
    ("MEA price (Rs/kg: 100 / 250)", ("opex", "mea_price_inr_kg"), 100.0, 250.0),
    ("Heat of absorption (kJ/mol: 80 / 90)", ("solvent", "dH_abs_kj_mol"), 80.0, 90.0),
    ("Turbine efficiency (0.80 / 0.90)", ("coal_plant", "turbine_eta"), 0.80, 0.90),
]

CEMENT_CASES = [
    ("Boiler fuel (Rs/GJ: 250 / 500)", ("cement_plant", "boiler_fuel_price_inr_gj"), 250.0, 500.0),
    ("Grid power (Rs/kWh: 5 / 9)", ("cement_plant", "elec_price_inr_kwh"), 5.0, 9.0),
    ("WACC (8% / 12%)", ("finance", "wacc"), 0.08, 0.12),
    ("Capture rate (80% / 95%)", ("cement_plant", "capture_rate"), 0.80, 0.95),
    ("Lean loading (0.20 / 0.28)", ("cement_plant", "alpha_lean"), 0.20, 0.28),
    ("Capex location factor (0.35 / 0.70)", ("capex", "loc_island"), 0.35, 0.70),
    ("Kiln flue gas CO2 (vol%: 16 / 25)", ("cement_plant", "y_co2"), 0.16, 0.25),
    ("MEA price (Rs/kg: 100 / 250)", ("opex", "mea_price_inr_kg"), 100.0, 250.0),
    ("Grid emission factor (t/MWh: 0.60 / 0.85)", ("cement_plant", "grid_ef_t_mwh"), 0.60, 0.85),
]


def tornado(case):
    cases = COAL_CASES if case == "coal" else CEMENT_CASES
    base = evaluate_coal(default_params()) if case == "coal" else evaluate_cement(default_params())
    rows = []
    for label, path, lo, hi in cases:
        r_lo, r_hi = _run(case, path, lo), _run(case, path, hi)
        row = {"parameter": label,
               "avoided_low": r_lo["cost_avoided_inr_t"] if r_lo else float("nan"),
               "avoided_high": r_hi["cost_avoided_inr_t"] if r_hi else float("nan"),
               "captured_low": r_lo["cost_captured_inr_t"] if r_lo else float("nan"),
               "captured_high": r_hi["cost_captured_inr_t"] if r_hi else float("nan")}
        if case == "coal":
            row["lcoe_incr_low"] = r_lo["lcoe_increase_inr_kwh"] if r_lo else float("nan")
            row["lcoe_incr_high"] = r_hi["lcoe_increase_inr_kwh"] if r_hi else float("nan")
        rows.append(row)
    df = pd.DataFrame(rows)
    df["swing"] = (df["avoided_high"] - df["avoided_low"]).abs()
    return base, df.sort_values("swing", ascending=False).reset_index(drop=True)


def sweep(case, path, values):
    rows = []
    for v in values:
        r = _run(case, path, v)
        if r is None:
            continue
        row = {"value": v,
               "reboiler_gj_per_t": r["design"]["reboiler_gj_per_t"],
               "cost_captured_inr_t": r["cost_captured_inr_t"],
               "cost_avoided_inr_t": r["cost_avoided_inr_t"]}
        if case == "coal":
            row["lcoe_increase_inr_kwh"] = r["lcoe_increase_inr_kwh"]
            row["efficiency_penalty_pts"] = r["efficiency_penalty_pts"]
        rows.append(row)
    return pd.DataFrame(rows)


def lean_loading_sweep(case="coal"):
    key = "coal_plant" if case == "coal" else "cement_plant"
    return sweep(case, (key, "alpha_lean"), [0.20, 0.22, 0.24, 0.26, 0.28, 0.30])


def capture_rate_sweep(case="coal"):
    key = "coal_plant" if case == "coal" else "cement_plant"
    return sweep(case, (key, "capture_rate"), [0.60, 0.70, 0.80, 0.85, 0.90, 0.95])


def coal_price_sweep():
    return sweep("coal", ("coal_plant", "coal_price_inr_t"),
                 [3000, 4000, 5000, 6000, 7000, 8000])
