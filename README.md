# CO2-Capture-cost-model-for-Indian-coal-power-and-cement-plants
I built a cost model that sits on top of a 30 wt% MEA capture unit and asks what it would take to fit one to an Indian coal plant or a cement works.

## What it does

It runs two plants side by side.

- A 660 MW supercritical coal unit, capturing 90% of its CO2.
- A cement plant making 6,000 tonnes of clinker a day, also at 90% capture. Steam comes from a separate coal boiler, and the CO2 from that boiler gets captured too.

For each one it works out the solvent circulation, the reboiler heat, the electricity the plant loses, the capital and running costs, and the cost per tonne of CO2. For coal it also gives the new cost of electricity. For cement it gives the extra cost per tonne of cement. After that it changes the inputs one at a time to see which ones matter, and draws the charts.

## What I got with the default inputs

| | Coal plant | Cement plant |
|---|---|---|
| Regeneration energy (GJ per tonne CO2) | 3.62 | 3.60 |
| Cost per tonne captured (Rs) | 3,439 | 5,054 |
| Cost per tonne avoided (Rs) | 5,567 | 10,038 |
| Cost per tonne avoided (USD) | 63 | 114 |
| Electricity cost | Rs 4.85 to Rs 9.30 per kWh | not applicable |
| Added cost per tonne of cement | not applicable | about Rs 4,000 |

On the coal side, a 660 MW unit drops to about 485 MW once capture is running, and efficiency falls from 35.8% to 26.3%. On the cement side, only about 71% of the kiln's CO2 is really avoided, even with 90% capture. The steam boiler and the grid power for compression both add emissions of their own.

The input that moves the answer most is the capital cost location factor. Changing it swings the coal avoided cost from roughly Rs 5,050 to Rs 6,870 per tonne. Load factor, coal price and cost of capital come after that.

## Running it

You need Python 3.9 or newer. These are for Windows Command Prompt, and you should run them one at a time.

```
cd C:\ccs_india
py -m venv venv
venv\Scripts\activate
py -m pip install -r requirements.txt
py run_all.py
```

It finishes in a few seconds and writes everything to an `outputs` folder next to the scripts.

One thing I ran into: don't put the project inside OneDrive. The virtual environment is thousands of tiny files and OneDrive tries to sync every one of them. A plain folder on the C drive worked fine.

## Changing the numbers

All the inputs are in `config.py`, grouped by topic. I didn't bury any numbers in the other files. If you want a different coal price, discount rate or capture rate, edit it there and run `run_all.py` again.

## What comes out

- `report.txt` is the full printed summary, with a comparison against literature ranges
- `summary.csv` and `results.json` hold the headline numbers and all the intermediate values
- `tornado_coal.csv` and `tornado_cement.csv` are the sensitivity tables
- three sweep files cover lean loading, capture rate and coal price
- seven PNG charts

## Things that aren't solid yet

I'd rather say these now than have someone find them later.

- The absorber is a short-cut model, not a full rate-based simulation. The equilibrium is a simple fit pinned at one point, and mass transfer uses one lumped coefficient that I tuned until the absorber came out around 16 m tall. It gives typical energy numbers, but I haven't checked it against measured equilibrium data.
- Capital cost is scaled from a reference value with an India location factor. That is an estimate, not a quote from a vendor. It matters more than any other input.
- The lean loading sweep shows reboiler duty rising steadily with lean loading, so the lowest loading always looks best. A real stripper has an optimum, because a lower loading needs a taller column, and I haven't modelled that. Don't read 0.20 as the best design.
- Transport and storage aren't included. The costs stop at CO2 compressed to 110 bar.
- For electricity cost, the coal case treats the plant as a new build. A retrofit on a plant that's already paid off would look different.
- My rupee figures come out well above older Indian studies. Some of that could be inflation, but I couldn't reproduce their inputs, so I'm not claiming the model agrees with them. In dollars, the coal result sits inside the 60 to 90 dollars per tonne people usually quote worldwide.
- The exchange rate, coal price and cement plant inputs are my own assumptions. Check them before using these numbers for anything formal.

## Repository structure

```
ccs_india/
├── README.md                 this file
├── requirements.txt          numpy, pandas, matplotlib
├── config.py                 every input and assumption
├── thermo.py                 water vapour pressure, MEA equilibrium fit, compression work
├── capture_process.py        absorber and stripper short-cut model, reboiler duty, power use
├── economics.py              capital recovery factor, capex scaling, consumables
├── coal_plant.py             coal case: energy penalty, electricity cost, cost per tonne
├── cement_plant.py           cement case: boiler loop, emissions avoided, cost per tonne
├── sensitivity.py            one-at-a-time sensitivities and sweeps
├── report.py                 makes the charts
├── run_all.py                runs everything and fills the outputs folder
├── docs/
│   ├── CO2_Capture_Cost_Report.docx
└── outputs/                  created when you run run_all.py
    ├── report.txt
    ├── summary.csv
    ├── results.json
    ├── tornado_coal.csv
    ├── tornado_cement.csv
    ├── sweep_lean_loading_coal.csv
    ├── sweep_capture_rate_coal.csv
    ├── sweep_coal_price.csv
    └── fig1 to fig7 (.png)
```

## Author

**Pratyush Dash**

B.Tech Chemical Engineering, KIIT University, Bhubaneswar 

