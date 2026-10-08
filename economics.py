"""
economics.py
Capital recovery, capex scaling and consumables for the capture unit.
"""


def crf(rate, years):
    """Capital recovery factor."""
    return rate * (1.0 + rate) ** years / ((1.0 + rate) ** years - 1.0)


def cepci_factor(P):
    m = P["macro"]
    return m["cepci_now"] / m["cepci_2020"]


def island_capex_inr(P, captured_t_h, y_co2):
    """Capture island (DCC, absorber, stripper, exchangers, solvent fill, utilities)."""
    c = P["capex"]
    usd = (c["island_ref_usd_2020"]
           * (captured_t_h / c["island_ref_t_h"]) ** c["scale_exp"]
           * (c["y_ref"] / y_co2) ** c["y_exp"])
    return usd * cepci_factor(P) * c["loc_island"] * P["macro"]["usd_inr"]


def compression_capex_inr(P, comp_kw):
    c = P["capex"]
    usd = c["comp_usd_per_kw_2020"] * comp_kw
    return usd * cepci_factor(P) * c["loc_comp"] * P["macro"]["usd_inr"]


def boiler_capex_inr(P, q_mw_th):
    c = P["capex"]
    usd = c["boiler_usd_per_kwth_2020"] * q_mw_th * 1000.0
    return usd * cepci_factor(P) * c["loc_island"] * P["macro"]["usd_inr"]


def consumables_inr_per_yr(P, captured_t_yr):
    o = P["opex"]
    per_t = o["mea_makeup_kg_per_t"] * o["mea_price_inr_kg"] + o["other_consumables_inr_per_t"]
    return per_t * captured_t_yr
