# LCA–TEA Decision Support Dashboard

Interactive Streamlit dashboard for integrated environmental and techno-economic assessment of three low-calorific landfill-gas utilisation pathways:

- Dual-Fuel Combustion
- Oxygen-Enriched Combustion
- SFR with CO₂ Capture

The dashboard combines deterministic LCA and TEA results with sensitivity analysis, Monte Carlo uncertainty propagation, probabilistic technology ranking, multi-impact environmental scoring, integrated environmental–economic decision robustness, and a CO₂-price policy threshold analysis for SFR.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/dashboard.py
```

## Repository structure

```text
app/dashboard.py
data/processed/lcia_results.csv
data/processed/hotspots.csv
data/processed/tea_summary.csv
data/processed/tea_cashflows.csv
requirements.txt
.streamlit/config.toml
```

## Deployment

For Streamlit Community Cloud, select this GitHub repository and set the app entry point to:

```text
app/dashboard.py
```

## Methodological note

This repository is a decision-support demonstration based on processed study data and documented modelling assumptions. Environmental category weights, economic assumptions, uncertainty distributions, and policy thresholds should be re-justified for any new real-world project or decision context.
