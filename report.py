"""
report.py
Figures (PNG) for the CO2 capture cost study.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = ["#1f4e79", "#2e86c1", "#85c1e9", "#e67e22", "#7d3c98"]


def fig_energy(coal, cement, path):
    labels = ["Coal plant", "Cement plant"]
    parts = ["desorption", "sensible", "stripping_steam"]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    bottom = [0.0, 0.0]
    for i, k in enumerate(parts):
        vals = [coal["design"]["reboiler_split_gj_per_t"][k],
                cement["design"]["reboiler_split_gj_per_t"][k]]
        ax.bar(labels, vals, bottom=bottom, color=COLORS[i], label=k.replace("_", " "))
        bottom = [b + v for b, v in zip(bottom, vals)]
    for x, b in zip(labels, bottom):
        ax.text(x, b + 0.05, "%.2f" % b, ha="center", fontweight="bold")
    ax.set_ylabel("Regeneration energy (GJ per t CO2)")
    ax.set_title("Solvent regeneration energy")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_cost(coal, cement, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), sharey=False)
    for ax, res, title in zip(axes, [coal, cement], ["Coal plant", "Cement plant"]):
        bd = res["cost_captured_breakdown"]
        bottom = 0.0
        for i, (k, v) in enumerate(bd.items()):
            ax.bar([title], [v], bottom=bottom, color=COLORS[i % len(COLORS)],
                   label="%s (%.0f)" % (k.replace("_", " "), v))
            bottom += v
        ax.set_ylabel("Rs per t CO2 captured")
        ax.set_title("%s: %.0f Rs/t captured, %.0f Rs/t avoided" %
                     (title, res["cost_captured_inr_t"], res["cost_avoided_inr_t"]), fontsize=10)
        ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_lcoe(coal, path):
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    vals = [coal["lcoe_ref_inr_kwh"], coal["lcoe_capture_inr_kwh"]]
    ax.bar(["Without capture", "With 90% capture"], vals, color=[COLORS[0], COLORS[3]])
    for i, v in enumerate(vals):
        ax.text(i, v + 0.1, "Rs %.2f" % v, ha="center", fontweight="bold")
    ax.set_ylabel("LCOE (Rs per kWh)")
    ax.set_title("Coal electricity cost: +Rs %.2f/kWh (+%.0f%%)" %
                 (coal["lcoe_increase_inr_kwh"], coal["lcoe_increase_pct"]))
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_tornado(base, df, path, title):
    d = df.iloc[::-1]
    b = base["cost_avoided_inr_t"]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    for i, (_, row) in enumerate(d.iterrows()):
        lo, hi = row["avoided_low"], row["avoided_high"]
        ax.barh(i, hi - b, left=b, color=COLORS[3], alpha=0.85)
        ax.barh(i, lo - b, left=b, color=COLORS[1], alpha=0.85)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d["parameter"], fontsize=8)
    ax.axvline(b, color="k", lw=1)
    ax.set_xlabel("Cost of CO2 avoided (Rs/t)   [blue = low value, orange = high value]")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_sweeps(lean_df, rate_df, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    ax = axes[0]
    ax.plot(lean_df["value"], lean_df["reboiler_gj_per_t"], "o-", color=COLORS[0])
    ax.set_xlabel("Lean loading (mol CO2 / mol MEA)")
    ax.set_ylabel("Reboiler duty (GJ/t CO2)")
    ax.set_title("Coal case: lean loading")
    ax2 = axes[1]
    ax2.plot(rate_df["value"] * 100, rate_df["cost_avoided_inr_t"], "o-", color=COLORS[3])
    ax2.set_xlabel("Capture rate (%)")
    ax2.set_ylabel("Cost of CO2 avoided (Rs/t)")
    ax2.set_title("Coal case: capture rate")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_coal_price(df, path):
    fig, ax = plt.subplots(figsize=(6, 4.3))
    ax.plot(df["value"], df["lcoe_increase_inr_kwh"], "o-", color=COLORS[0])
    ax.set_xlabel("Landed coal price (Rs/t)")
    ax.set_ylabel("Increase in electricity cost (Rs/kWh)")
    ax.set_title("Electricity cost impact vs coal price")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def make_all(coal, cement, tor_coal, tor_cement, lean_df, rate_df, price_df, outdir):
    os.makedirs(outdir, exist_ok=True)
    j = lambda n: os.path.join(outdir, n)
    fig_energy(coal, cement, j("fig1_regeneration_energy.png"))
    fig_cost(coal, cement, j("fig2_cost_breakdown.png"))
    fig_lcoe(coal, j("fig3_coal_lcoe.png"))
    fig_tornado(coal, tor_coal, j("fig4_tornado_coal.png"), "Coal: sensitivity of cost of CO2 avoided")
    fig_tornado(cement, tor_cement, j("fig5_tornado_cement.png"), "Cement: sensitivity of cost of CO2 avoided")
    fig_sweeps(lean_df, rate_df, j("fig6_coal_sweeps.png"))
    fig_coal_price(price_df, j("fig7_coal_price_vs_lcoe.png"))
