"""
config.py
Every number used by the CO2 capture cost model lives here.
Nothing needs to be filled in. Change a value here and re-run run_all.py.

Units: kPa, K, kJ, kg, t, INR unless the key name says otherwise.
Where a value is an engineering assumption (not a measured plant number),
the comment says so. These are the numbers to defend or change in a paper.
"""
import copy


def default_params():
    """Return a fresh deep copy so sensitivity runs never modify the base case."""
    return copy.deepcopy(_P)


_P = {
    # ------------------------------------------------------------------
    "macro": {
        "usd_inr": 88.0,          # assumed exchange rate
        "cepci_2020": 596.2,      # Chemical Engineering Plant Cost Index, 2020 annual
        "cepci_now": 800.0,       # approx. 2023-24 level
    },
    # ------------------------------------------------------------------
    "solvent": {                  # 30 wt% aqueous MEA
        "mea_wt_frac": 0.30,
        "cp_kj_kg_k": 3.7,        # loaded 30 wt% MEA, typical 3.5-3.9
        "density_kg_m3": 1070.0,
        "dH_abs_kj_mol": 85.0,    # heat of CO2 absorption in MEA, typical 82-88
        # Simplified carbamate-type VLE:  ln P = A + B/T + n*ln(a/(1-2a))
        # B = -dH/R. A is computed so that P*(40 C, alpha=0.20) = 0.05 kPa,
        # a literature-typical point for 30 wt% MEA. n = 1.7 sets the steepness.
        "vle_anchor_p_kpa": 0.05,
        "vle_anchor_T_K": 313.15,
        "vle_anchor_alpha": 0.20,
        "vle_n": 1.7,
        "x_water": 0.85,          # effective water activity in loaded solvent
    },
    # ------------------------------------------------------------------
    "process": {
        "P_abs_kpa": 110.0,       # absorber inlet pressure
        "T_abs_K": 323.15,        # mean absorber temperature (50 C, isothermal)
        "rich_approach": 0.90,    # rich loading = lean + 0.90*(equilibrium - lean)
        "T_reb_K": 393.15,        # reboiler 120 C
        "P_reb_kpa": 200.0,
        "dT_cross_K": 10.0,       # cross-exchanger approach
        "T_top_K": 375.15,        # stripper overhead 102 C
        "P_top_kpa": 190.0,
        "dh_vap_kj_mol": 40.6,    # water latent heat near 100 C
        "gas_velocity_m_s": 2.0,  # superficial velocity, structured packing
        "kga_eff": 0.11e-3,       # lumped overall KGa, kmol/(m3 s kPa). Engineering
                                  # assumption giving 15-20 m packing, typical of
                                  # industrial 90% capture. Replace with your
                                  # Phase-1 rate-based value if you want.
        "d_max_m": 12.0,          # largest practical absorber diameter
        "dp_blower_kpa": 9.0,     # flue gas pressure drop (DCC + absorber + ducts)
        "eta_blower": 0.75,
        "eta_pump": 0.75,
        "pump_head_kpa": 850.0,   # lean + rich circuits combined
        "cw_head_kpa": 400.0,
        "cw_dT_K": 10.0,
        "cw_cp_kj_kg_k": 4.18,
    },
    # ------------------------------------------------------------------
    "compression": {              # CO2 from 1.5 bar to 110 bar, 5 stages
        "p_in_kpa": 150.0,
        "p_out_kpa": 11000.0,
        "stages": 5,
        "T_in_K": 313.15,
        "gamma": 1.29,
        "eta": 0.80,
        "real_gas_factor": 1.08,  # covers non-ideal behaviour in high-pressure stages
        "heat_rejected_frac": 0.95,
    },
    # ------------------------------------------------------------------
    "finance": {
        "wacc": 0.10,
        "capture_life_yr": 25,
    },
    # ------------------------------------------------------------------
    "capex": {
        # Capture island = DCC + absorber + stripper + exchangers + solvent fill + utilities
        "island_ref_usd_2020": 560e6,   # reference cost at 400 t/h captured, 13% CO2
        "island_ref_t_h": 400.0,
        "scale_exp": 0.67,
        "y_ref": 0.13,
        "y_exp": 0.25,                  # higher CO2 concentration -> smaller equipment
        "loc_island": 0.45,             # India vs OECD cost basis: Indian SC plant costs ~0.38x OECD, island part-imported
        "comp_usd_per_kw_2020": 1800.0, # compression + dehydration, installed
        "loc_comp": 0.85,
        "boiler_usd_per_kwth_2020": 100.0,  # dedicated steam boiler (cement case)
        "tci_factor": 1.15,             # owner's cost + contingency + IDC
        "fom_frac": 0.04,               # fixed O&M as fraction of capture TCI per year
    },
    "opex": {
        "mea_makeup_kg_per_t": 1.5,     # degradation + slip, kg MEA per t CO2 captured
        "mea_price_inr_kg": 150.0,
        "other_consumables_inr_per_t": 45.0,  # water, NaOH, carbon filters, reclaimer waste
    },
    # ------------------------------------------------------------------
    "coal_plant": {
        "net_mw": 660.0,                # typical Indian supercritical unit
        "heat_rate_kcal_kwh": 2400.0,   # net heat rate on GCV (efficiency ~35.8%)
        "coal_gcv_kcal_kg": 3800.0,     # typical Indian domestic thermal coal
        "coal_c_frac": 0.40,            # carbon mass fraction, as received
        "coal_price_inr_t": 5000.0,     # landed cost at plant
        "plf": 0.80,
        "base_capex_inr_per_kw": 80000.0,  # 8 crore per MW
        "base_fom_frac": 0.025,
        "base_vom_inr_kwh": 0.15,
        "y_co2": 0.13,                  # CO2 vol fraction after FGD
        "capture_rate": 0.90,
        "alpha_lean": 0.22,
        "T_cond_K": 318.15,             # LP turbine exhaust, 45 C (hot climate)
        "turbine_eta": 0.85,
        "dT_steam_K": 10.0,             # extraction steam saturation above reboiler T
    },
    # ------------------------------------------------------------------
    "cement_plant": {
        "clinker_tpd": 6000.0,
        "kiln_days": 330.0,
        "clinker_factor": 0.70,         # clinker / cement
        "process_co2_t_per_t_clk": 0.52,
        "thermal_gj_per_t_clk": 3.0,
        "kiln_fuel_ef_kg_gj": 95.0,     # coal/petcoke mix
        "y_co2": 0.20,                  # kiln flue gas, wet basis
        "capture_rate": 0.90,
        "alpha_lean": 0.22,
        "boiler_eff": 0.85,
        "boiler_fuel_price_inr_gj": 380.0,
        "boiler_ef_kg_gj": 94.6,
        "boiler_y_co2": 0.14,
        "elec_price_inr_kwh": 7.0,
        "grid_ef_t_mwh": 0.72,
        "dT_steam_K": 10.0,
    },
    # ------------------------------------------------------------------
    # Literature ranges used only for the comparison table printed by run_all.py
    "literature": {
        "reboiler_gj_per_t_low": 3.5,
        "reboiler_gj_per_t_high": 4.0,
        "india_coal_incr_coe_inr_kwh_low": 2.2,     # Energy Procedia 54 (Indian case studies)
        "india_coal_incr_coe_inr_kwh_high": 2.6,
        "india_coal_avoided_inr_t_low": 2600.0,
        "india_coal_avoided_inr_t_high": 3200.0,
        "efficiency_penalty_pts_low": 8.0,
        "efficiency_penalty_pts_high": 12.0,
        "compression_kwh_per_t_low": 90.0,
        "compression_kwh_per_t_high": 120.0,
    },
}
