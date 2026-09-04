from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="LCA–TEA Decision Support Dashboard",
    layout="wide"
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

LCIA_CSV = PROCESSED_DIR / "lcia_results.csv"
HOTSPOTS_CSV = PROCESSED_DIR / "hotspots.csv"
TEA_SUMMARY_CSV = PROCESSED_DIR / "tea_summary.csv"
TEA_CASHFLOWS_CSV = PROCESSED_DIR / "tea_cashflows.csv"


# ============================================================
# LOAD PROCESSED DATA
# ============================================================

@st.cache_data
def load_processed_data():

    lcia = pd.read_csv(LCIA_CSV)

    hotspots = pd.read_csv(HOTSPOTS_CSV)

    tea_summary = pd.read_csv(
        TEA_SUMMARY_CSV
    )

    tea_cashflows = pd.read_csv(
        TEA_CASHFLOWS_CSV
    )

    return (
        lcia,
        hotspots,
        tea_summary,
        tea_cashflows
    )


(
    lcia_processed,
    hotspots_processed,
    tea_summary,
    tea_cashflows
) = load_processed_data()


# ============================================================
# TITLE
# ============================================================

st.title("LCA–TEA Decision Support Dashboard")

st.caption(
    "Integrated Environmental–Economic Assessment "
    "with Uncertainty and Decision Support"
)


# ============================================================
# MASTER LCA DATA
# ============================================================

master_df = lcia_processed.copy()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Analysis Settings")

impact_categories = sorted(
    master_df["Impact category"]
    .dropna()
    .unique()
)

selected_impact = st.sidebar.selectbox(
    "Impact category",
    impact_categories,
    index=impact_categories.index(
        "Climate change"
    )
)


# ============================================================
# MODULE 1 — ENVIRONMENTAL PERFORMANCE
# ============================================================

selected_df = master_df[
    master_df["Impact category"]
    == selected_impact
].copy()

selected_df = selected_df.sort_values(
    "Result"
)

reference_unit = selected_df[
    "Reference unit"
].iloc[0]

best_row = selected_df.iloc[0]

worst_row = selected_df.iloc[-1]


st.header("Environmental Performance")


# ------------------------------------------------------------
# KPI CARDS
# ------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Best Technology",
    best_row["Technology"]
)

col2.metric(
    "Lowest Impact",
    f"{best_row['Result']:.4f}",
    reference_unit
)

col3.metric(
    "Highest Impact",
    f"{worst_row['Result']:.4f}",
    reference_unit
)

difference_pct = (
    (
        worst_row["Result"]
        - best_row["Result"]
    )
    / worst_row["Result"]
    * 100
)

col4.metric(
    "Best vs Worst",
    f"{difference_pct:.1f}% lower"
)


# ------------------------------------------------------------
# COMPARISON CHART
# ------------------------------------------------------------

st.subheader(
    f"Technology Comparison — {selected_impact}"
)

fig = px.bar(
    selected_df,
    x="Technology",
    y="Result",
    text="Result",
    hover_data=[
        "Reference unit"
    ],
    labels={
        "Result": reference_unit,
        "Technology": ""
    }
)

fig.update_traces(
    texttemplate="%{text:.4f}",
    textposition="outside"
)

fig.update_layout(
    height=500,
    yaxis_title=reference_unit
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ------------------------------------------------------------
# RESULT TABLE
# ------------------------------------------------------------

st.subheader("Comparison Table")

display_df = selected_df[
    [
        "Technology",
        "Impact category",
        "Reference unit",
        "Result"
    ]
].copy()

display_df["Rank"] = range(
    1,
    len(display_df) + 1
)

display_df = display_df[
    [
        "Rank",
        "Technology",
        "Impact category",
        "Reference unit",
        "Result"
    ]
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ------------------------------------------------------------
# INTERPRETATION
# ------------------------------------------------------------

st.subheader("Interpretation")

st.success(
    f"For {selected_impact}, "
    f"{best_row['Technology']} has the lowest impact "
    f"at {best_row['Result']:.4f} "
    f"{reference_unit}."
)

st.caption(
    "Lower LCIA values are interpreted as lower "
    "environmental burden for the selected midpoint "
    "impact category."
)


# ============================================================
# MODULE 2 — ENVIRONMENTAL HOTSPOTS
# ============================================================

st.divider()

st.header("Environmental Hotspot Analysis")

hotspot_col1, hotspot_col2 = st.columns(2)

selected_technology = hotspot_col1.selectbox(
    "Technology",
    sorted(
        hotspots_processed[
            "Technology"
        ]
        .dropna()
        .unique()
    ),
    key="hotspot_technology"
)

selected_hotspot_impact = hotspot_col2.selectbox(
    "Impact category",
    impact_categories,
    index=impact_categories.index(
        "Climate change"
    ),
    key="hotspot_impact"
)


selected_rows = hotspots_processed[
    (
        hotspots_processed["Technology"]
        == selected_technology
    )
    &
    (
        hotspots_processed["Impact category"]
        == selected_hotspot_impact
    )
].copy()


if selected_rows.empty:

    st.error(
        "Selected impact category was not found "
        "in processed hotspot data."
    )

else:

    contributions = selected_rows.copy()


    # --------------------------------------------------------
    # TOTAL RESULT
    # --------------------------------------------------------

    total_result_row = master_df[
        (
            master_df["Technology"]
            == selected_technology
        )
        &
        (
            master_df["Impact category"]
            == selected_hotspot_impact
        )
    ]

    total_result = (
        total_result_row["Result"]
        .iloc[0]
    )

    hotspot_unit = (
        total_result_row[
            "Reference unit"
        ]
        .iloc[0]
    )


    # --------------------------------------------------------
    # POSITIVE / NEGATIVE CONTRIBUTIONS
    # --------------------------------------------------------

    positive = contributions[
        contributions["Contribution"] > 0
    ].copy()

    negative = contributions[
        contributions["Contribution"] < 0
    ].copy()

    positive = positive.sort_values(
        "Contribution",
        ascending=False
    )

    positive_total = (
        positive["Contribution"].sum()
    )

    negative_total = (
        negative["Contribution"].sum()
    )

    direct_sum = (
        contributions["Contribution"].sum()
    )

    reconciliation_difference = (
        direct_sum - total_result
    )


    # --------------------------------------------------------
    # HOTSPOT METRICS
    # --------------------------------------------------------

    positive["Share of LCIA (%)"] = (
        positive["Contribution"]
        / total_result
        * 100
    )

    positive[
        "Share of Positive (%)"
    ] = (
        positive["Contribution"]
        / positive_total
        * 100
    )

    positive[
        "Cumulative Positive (%)"
    ] = (
        positive[
            "Share of Positive (%)"
        ].cumsum()
    )

    positive["Rank"] = range(
        1,
        len(positive) + 1
    )

    top_process = positive.iloc[0]

    processes_to_80 = (
        positive[
            positive[
                "Cumulative Positive (%)"
            ] < 80
        ].shape[0]
        + 1
    )


    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    st.subheader(
        f"{selected_technology} — "
        f"{selected_hotspot_impact}"
    )

    h1, h2, h3, h4 = st.columns(4)

    h1.metric(
        "LCIA Total",
        f"{total_result:.4f}"
    )

    h1.caption(
        hotspot_unit
    )

    h2.metric(
        "Non-zero Processes",
        f"{len(contributions):,}"
    )

    h3.metric(
        "Largest Hotspot",
        f"{top_process['Share of Positive (%)']:.1f}%"
    )

    h3.caption(
        str(
            top_process["Process"]
        )[:55]
    )

    h4.metric(
        "Processes for 80%",
        f"{processes_to_80}"
    )


    # --------------------------------------------------------
    # TOP 10 HOTSPOTS
    # --------------------------------------------------------

    st.subheader(
        "Top 10 Environmental Hotspots"
    )

    top10 = positive.head(10).copy()

    top10["Process Short"] = (
        top10["Process"]
        .astype(str)
        .str.slice(0, 75)
    )

    hotspot_fig = px.bar(
        top10.sort_values(
            "Contribution"
        ),
        x="Contribution",
        y="Process Short",
        orientation="h",
        text="Share of Positive (%)",
        hover_data={
            "Process": True,
            "Location": True,
            "Contribution": ":.6f",
            "Share of LCIA (%)": ":.2f",
            "Share of Positive (%)": ":.2f",
            "Cumulative Positive (%)": ":.2f"
        },
        labels={
            "Contribution": hotspot_unit,
            "Process Short": ""
        }
    )

    hotspot_fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    hotspot_fig.update_layout(
        height=600,
        yaxis_title="",
        xaxis_title=hotspot_unit
    )

    st.plotly_chart(
        hotspot_fig,
        use_container_width=True
    )


    # --------------------------------------------------------
    # PARETO ANALYSIS
    # --------------------------------------------------------

    st.subheader(
        "Cumulative Hotspot Coverage"
    )

    pareto = positive.head(20).copy()

    pareto_fig = px.line(
        pareto,
        x="Rank",
        y="Cumulative Positive (%)",
        markers=True,
        labels={
            "Rank": "Hotspot Rank",
            "Cumulative Positive (%)":
                "Cumulative Contribution (%)"
        }
    )

    pareto_fig.add_hline(
        y=80,
        line_dash="dash",
        annotation_text="80% threshold"
    )

    pareto_fig.update_layout(
        height=400,
        yaxis_range=[0, 105]
    )

    st.plotly_chart(
        pareto_fig,
        use_container_width=True
    )


    # --------------------------------------------------------
    # HOTSPOT TABLE
    # --------------------------------------------------------

    st.subheader(
        "Hotspot Ranking"
    )

    hotspot_table = positive[
        [
            "Rank",
            "Process",
            "Location",
            "Contribution",
            "Share of LCIA (%)",
            "Share of Positive (%)",
            "Cumulative Positive (%)"
        ]
    ].head(20).copy()

    hotspot_table = (
        hotspot_table.rename(
            columns={
                "Contribution":
                    f"Contribution ({hotspot_unit})"
            }
        )
    )

    st.dataframe(
        hotspot_table,
        use_container_width=True,
        hide_index=True
    )


    # --------------------------------------------------------
    # DATA QUALITY CHECK
    # --------------------------------------------------------

    st.subheader(
        "Data Quality Check"
    )

    qa1, qa2, qa3, qa4 = st.columns(4)

    qa1.metric(
        "Direct Sum",
        f"{direct_sum:.6f}"
    )

    qa2.metric(
        "LCIA Total",
        f"{total_result:.6f}"
    )

    qa3.metric(
        "Difference",
        f"{reconciliation_difference:.6f}"
    )

    qa4.metric(
        "Negative Contributions",
        f"{negative_total:.6f}"
    )

    st.caption(
        "Hotspot ranking is based on positive direct impact "
        "contributions. Negative contributions are reported "
        "separately to avoid mixing burdens and credits."
    )


# ============================================================
# MODULE 3 — TECHNO-ECONOMIC ANALYSIS
# ============================================================

st.divider()

st.header("Techno-Economic Analysis")


# ------------------------------------------------------------
# FINANCIAL KPI COMPARISON
# ------------------------------------------------------------

st.subheader(
    "Financial Performance Comparison"
)

best_npv = tea_summary.loc[
    tea_summary["NPV (€)"].idxmax()
]

best_irr = tea_summary.loc[
    tea_summary["IRR"].idxmax()
]

best_payback = tea_summary.loc[
    tea_summary[
        "Discounted Payback (years)"
    ].idxmin()
]

best_capex = tea_summary.loc[
    tea_summary["CAPEX (€)"].idxmin()
]


t1, t2, t3, t4 = st.columns(4)

t1.metric(
    "Highest NPV",
    f"€{best_npv['NPV (€)']:,.0f}"
)

t1.caption(
    best_npv["Technology"]
)

t2.metric(
    "Highest IRR",
    f"{best_irr['IRR'] * 100:.2f}%"
)

t2.caption(
    best_irr["Technology"]
)

t3.metric(
    "Shortest Payback",
    f"{best_payback['Discounted Payback (years)']:.2f} years"
)

t3.caption(
    best_payback["Technology"]
)

t4.metric(
    "Lowest CAPEX",
    f"€{best_capex['CAPEX (€)']:,.0f}"
)

t4.caption(
    best_capex["Technology"]
)


# ------------------------------------------------------------
# NPV COMPARISON
# ------------------------------------------------------------

st.subheader(
    "Net Present Value"
)

npv_fig = px.bar(
    tea_summary.sort_values(
        "NPV (€)"
    ),
    x="Technology",
    y="NPV (€)",
    text="NPV (€)",
    labels={
        "Technology": "",
        "NPV (€)": "NPV (€)"
    }
)

npv_fig.update_traces(
    texttemplate="€%{text:,.0f}",
    textposition="outside"
)

npv_fig.update_layout(
    height=450
)

st.plotly_chart(
    npv_fig,
    use_container_width=True
)


# ------------------------------------------------------------
# FINANCIAL TABLE
# ------------------------------------------------------------

st.subheader(
    "Financial Indicators"
)

tea_display = tea_summary[
    [
        "Technology",
        "CAPEX (€)",
        "NPV (€)",
        "IRR",
        "Discounted Payback (years)",
        "Discount rate",
        "Project lifetime (years)"
    ]
].copy()

tea_display["IRR (%)"] = (
    tea_display["IRR"] * 100
)

tea_display[
    "Discount rate (%)"
] = (
    tea_display["Discount rate"]
    * 100
)

tea_display = tea_display.drop(
    columns=[
        "IRR",
        "Discount rate"
    ]
)

tea_display = tea_display[
    [
        "Technology",
        "CAPEX (€)",
        "NPV (€)",
        "IRR (%)",
        "Discounted Payback (years)",
        "Discount rate (%)",
        "Project lifetime (years)"
    ]
]

st.dataframe(
    tea_display,
    use_container_width=True,
    hide_index=True
)


# ------------------------------------------------------------
# CASH FLOW ANALYSIS
# ------------------------------------------------------------

st.subheader(
    "Discounted Cash Flow"
)

tea_technology = st.selectbox(
    "Technology for cash-flow analysis",
    sorted(
        tea_cashflows[
            "Technology"
        ]
        .dropna()
        .unique()
    ),
    key="tea_technology"
)

selected_cashflow = tea_cashflows[
    tea_cashflows["Technology"]
    == tea_technology
].copy()

annual_cashflow = selected_cashflow[
    selected_cashflow["t"] > 0
].copy()


cashflow_fig = px.line(
    annual_cashflow,
    x="Year",
    y=[
        "Revenue (€)",
        "OPEX (€)",
        "FCF (€)"
    ],
    markers=True,
    labels={
        "value": "€ / year",
        "variable": ""
    }
)

cashflow_fig.update_layout(
    height=500,
    legend_title_text=""
)

st.plotly_chart(
    cashflow_fig,
    use_container_width=True
)


# ------------------------------------------------------------
# CUMULATIVE DISCOUNTED CASH FLOW
# ------------------------------------------------------------

st.subheader(
    "Cumulative Discounted Cash Flow"
)

cum_fig = px.line(
    annual_cashflow,
    x="Year",
    y="Cumulative PV (€)",
    markers=True,
    labels={
        "Cumulative PV (€)":
            "Cumulative PV (€)"
    }
)

capex_row = tea_summary[
    tea_summary["Technology"]
    == tea_technology
].iloc[0]

initial_investment = (
    capex_row["CAPEX (€)"]
    + capex_row["Working capital (€)"]
)

cum_fig.add_hline(
    y=initial_investment,
    line_dash="dash",
    annotation_text="Investment recovery threshold"
)

cum_fig.update_layout(
    height=450
)

st.plotly_chart(
    cum_fig,
    use_container_width=True
)


# ------------------------------------------------------------
# TEA INTERPRETATION
# ------------------------------------------------------------

st.subheader(
    "Economic Interpretation"
)

st.success(
    f"{best_npv['Technology']} currently provides "
    f"the highest deterministic NPV "
    f"(€{best_npv['NPV (€)']:,.0f}) "
    f"and an IRR of "
    f"{best_npv['IRR'] * 100:.2f}%."
)

st.caption(
    "These results represent deterministic TEA outcomes. "
    "Uncertainty, sensitivity analysis, probability of economic "
    "success and ranking robustness will be added in the next "
    "decision-support stage."
)
# ============================================================
# MODULE 4 — INTEGRATED DETERMINISTIC LCA–TEA
# ============================================================

st.divider()

st.header("Integrated LCA–TEA Decision Analysis")

st.caption(
    "Deterministic integration of environmental and economic "
    "performance before sensitivity and uncertainty analysis."
)


# ------------------------------------------------------------
# PREPARE INTEGRATED DATA
# ------------------------------------------------------------

climate_df = master_df[
    master_df["Impact category"] == "Climate change"
][
    [
        "Technology",
        "Result",
        "Reference unit"
    ]
].copy()

climate_df = climate_df.rename(
    columns={
        "Result": "Climate Impact"
    }
)

integrated_df = climate_df.merge(
    tea_summary,
    on="Technology",
    how="inner"
)

integrated_df["IRR (%)"] = (
    integrated_df["IRR"] * 100
)


# ------------------------------------------------------------
# PARETO DOMINANCE
# Lower environmental impact = better
# Higher NPV = better
# ------------------------------------------------------------

def is_dominated(row, df):

    for _, other in df.iterrows():

        if other["Technology"] == row["Technology"]:
            continue

        environmentally_better_or_equal = (
            other["Climate Impact"]
            <= row["Climate Impact"]
        )

        economically_better_or_equal = (
            other["NPV (€)"]
            >= row["NPV (€)"]
        )

        strictly_better_in_one = (
            other["Climate Impact"]
            < row["Climate Impact"]
            or
            other["NPV (€)"]
            > row["NPV (€)"]
        )

        if (
            environmentally_better_or_equal
            and economically_better_or_equal
            and strictly_better_in_one
        ):
            return True

    return False


integrated_df["Decision Status"] = (
    integrated_df.apply(
        lambda row:
            "Dominated"
            if is_dominated(row, integrated_df)
            else "Pareto-efficient",
        axis=1
    )
)


# ------------------------------------------------------------
# BASELINE KPI CARDS
# ------------------------------------------------------------

st.subheader("Baseline Integrated Decision")

pareto_df = integrated_df[
    integrated_df["Decision Status"]
    == "Pareto-efficient"
].copy()

best_environmental = integrated_df.loc[
    integrated_df[
        "Climate Impact"
    ].idxmin()
]

best_economic = integrated_df.loc[
    integrated_df[
        "NPV (€)"
    ].idxmax()
]

d1, d2, d3 = st.columns(3)

d1.metric(
    "Lowest Climate Impact",
    best_environmental["Technology"]
)

d1.caption(
    f"{best_environmental['Climate Impact']:.4f} "
    f"{best_environmental['Reference unit']}"
)

d2.metric(
    "Highest NPV",
    best_economic["Technology"]
)

d2.caption(
    f"€{best_economic['NPV (€)']:,.0f}"
)

d3.metric(
    "Pareto-efficient Alternatives",
    f"{len(pareto_df)} / {len(integrated_df)}"
)


# ------------------------------------------------------------
# ENVIRONMENTAL–ECONOMIC TRADE-OFF PLOT
# ------------------------------------------------------------

st.subheader(
    "Environmental–Economic Trade-off"
)

tradeoff_fig = px.scatter(
    integrated_df,
    x="Climate Impact",
    y="NPV (€)",
    text="Technology",
    size="IRR (%)",
    hover_data={
        "Technology": True,
        "Climate Impact": ":.4f",
        "NPV (€)": ":,.0f",
        "IRR (%)": ":.2f",
        "Discounted Payback (years)": ":.2f",
        "Decision Status": True
    },
    labels={
        "Climate Impact":
            "Climate Change Impact (kg CO2-Eq)",
        "NPV (€)":
            "Net Present Value (€)",
        "IRR (%)":
            "IRR (%)"
    }
)

tradeoff_fig.update_traces(
    textposition="top center"
)

tradeoff_fig.update_layout(
    height=550
)

st.plotly_chart(
    tradeoff_fig,
    use_container_width=True
)


# ------------------------------------------------------------
# INTEGRATED DECISION TABLE
# ------------------------------------------------------------

st.subheader(
    "Integrated Decision Matrix"
)

integrated_table = integrated_df[
    [
        "Technology",
        "Climate Impact",
        "Reference unit",
        "CAPEX (€)",
        "NPV (€)",
        "IRR (%)",
        "Discounted Payback (years)",
        "Decision Status"
    ]
].copy()

integrated_table = integrated_table.sort_values(
    [
        "Decision Status",
        "Climate Impact"
    ]
)

st.dataframe(
    integrated_table,
    use_container_width=True,
    hide_index=True
)


# ------------------------------------------------------------
# BASELINE INTERPRETATION
# ------------------------------------------------------------

st.subheader(
    "Baseline Decision Interpretation"
)

if (
    best_environmental["Technology"]
    == best_economic["Technology"]
):

    baseline_winner = (
        best_environmental["Technology"]
    )

    st.success(
        f"{baseline_winner} is the strongest deterministic "
        f"baseline alternative because it currently has both "
        f"the lowest climate-change impact and the highest NPV."
    )

else:

    st.warning(
        f"The deterministic baseline contains a trade-off. "
        f"{best_environmental['Technology']} has the lowest "
        f"climate impact, while "
        f"{best_economic['Technology']} has the highest NPV."
    )


dominated_list = integrated_df[
    integrated_df["Decision Status"]
    == "Dominated"
]["Technology"].tolist()

if dominated_list:

    st.info(
        "Dominated alternative(s): "
        + ", ".join(dominated_list)
        + ". These alternatives are inferior to at least one "
        "other technology in both climate impact and NPV "
        "under the current deterministic assumptions."
    )

else:

    st.info(
        "No technology is Pareto-dominated under the current "
        "deterministic climate-impact and NPV criteria."
    )


st.caption(
    "This is a deterministic baseline only. "
    "The next stage will test whether this decision remains "
    "stable when key model parameters are varied through "
    "sensitivity and uncertainty analysis."
)
# ============================================================
# MODULE 5 — TEA SENSITIVITY & DECISION-SWITCH ANALYSIS
# ============================================================

st.divider()

st.header("TEA Sensitivity & Decision-Switch Analysis")

st.caption(
    "One-at-a-Time (OAT) sensitivity analysis with selectable economic "
    "parameters. In addition to NPV influence, this module tests whether "
    "a parameter change can alter the technology with the highest NPV."
)


# ------------------------------------------------------------
# SENSITIVITY SETTINGS
# ------------------------------------------------------------

sensitivity_technology = st.selectbox(
    "Technology for detailed sensitivity curves",
    sorted(tea_summary["Technology"].dropna().unique()),
    key="sensitivity_technology"
)

sensitivity_range_pct = st.slider(
    "Sensitivity interval (±%)",
    min_value=5,
    max_value=50,
    value=20,
    step=5,
    key="sensitivity_range_pct"
)

st.caption(
    "Select the parameters to test. Direct TEA inputs and composite stress-test levers "
    "are complemented by a CO₂ price policy lever for the SFR pathway."
)

parameter_definitions = {
    "CAPEX": "Direct input",
    "OPEX": "Direct input",
    "Revenue": "Direct input",
    "Discount Rate": "Direct input",
    "Working Capital": "Direct input",
    "Tax Rate": "Direct input",
    "Annual Depreciation": "Direct input",
    "Total Investment Cost": "Composite: CAPEX + working capital",
    "Cost Inflation": "Composite: CAPEX + OPEX",
    "Operating Cost Burden": "Composite: OPEX + depreciation",
    "CO₂ Price Policy": "Policy lever: SFR CO₂-linked revenue (baseline €50/tCO₂)",
}

parameter_cols = st.columns(2)
selected_parameters = []

for i, (parameter, parameter_type) in enumerate(parameter_definitions.items()):
    default_selected = parameter in {
        "CAPEX",
        "OPEX",
        "Revenue",
        "Discount Rate",
    }

    with parameter_cols[i % 2]:
        if st.checkbox(
            f"{parameter}",
            value=default_selected,
            key=f"sens_param_{i}"
        ):
            selected_parameters.append(parameter)
        st.caption(parameter_type)

if not selected_parameters:
    st.warning("Select at least one sensitivity parameter to run the analysis.")
    st.stop()


# ------------------------------------------------------------
# GENERIC TEA NPV RECALCULATION
# ------------------------------------------------------------

# CO₂ policy mapping used in the original Monte Carlo model.
# At the baseline price of €50/tCO₂, the multiplier equals 1.0.
# The SFR gross-revenue series already contains CO₂-related revenue, so the
# policy lever scales only the CO₂-linked proxy share rather than adding a
# second revenue stream.
CO2_PRICE_BASE_EUR_T = 50.0
SFR_CO2_LINKED_REVENUE_SHARE = 0.30

def _is_sfr_technology(technology):
    return "sfr" in str(technology).lower()

def calculate_tea_npv_for_technology(
    technology,
    parameter=None,
    multiplier=1.0
):
    summary_row = tea_summary[
        tea_summary["Technology"] == technology
    ].iloc[0]

    cashflow_df = tea_cashflows[
        tea_cashflows["Technology"] == technology
    ].copy()

    cashflow_df["t"] = pd.to_numeric(
        cashflow_df["t"],
        errors="coerce"
    )

    annual_cf = cashflow_df[
        cashflow_df["t"] > 0
    ].copy()

    capex = float(summary_row["CAPEX (€)"])
    working_capital = float(summary_row["Working capital (€)"])
    depreciation = float(summary_row["Annual depreciation (€)"])
    tax_rate = float(summary_row["Tax rate"])
    discount_rate = float(summary_row["Discount rate"])

    revenue_multiplier = 1.0
    opex_multiplier = 1.0

    if parameter == "CAPEX":
        capex *= multiplier
        depreciation *= multiplier

    elif parameter == "OPEX":
        opex_multiplier = multiplier

    elif parameter == "Revenue":
        revenue_multiplier = multiplier

    elif parameter == "Discount Rate":
        discount_rate *= multiplier

    elif parameter == "Working Capital":
        working_capital *= multiplier

    elif parameter == "Tax Rate":
        tax_rate *= multiplier
        tax_rate = max(tax_rate, 0.0)

    elif parameter == "Annual Depreciation":
        depreciation *= multiplier

    elif parameter == "Total Investment Cost":
        capex *= multiplier
        working_capital *= multiplier
        depreciation *= multiplier

    elif parameter == "Cost Inflation":
        capex *= multiplier
        depreciation *= multiplier
        opex_multiplier = multiplier

    elif parameter == "Operating Cost Burden":
        opex_multiplier = multiplier
        depreciation *= multiplier

    elif parameter == "CO₂ Price Policy":
        # multiplier is interpreted relative to the baseline €50/tCO₂ price.
        # Only SFR receives the CO₂-linked policy revenue effect.
        if _is_sfr_technology(technology):
            co2_price_eur_t = CO2_PRICE_BASE_EUR_T * multiplier
            revenue_multiplier *= (
                (1.0 - SFR_CO2_LINKED_REVENUE_SHARE)
                + SFR_CO2_LINKED_REVENUE_SHARE
                * (co2_price_eur_t / CO2_PRICE_BASE_EUR_T)
            )

    npv_value = -(capex + working_capital)

    final_year = int(annual_cf["t"].max())

    for _, row in annual_cf.iterrows():
        t = int(row["t"])

        revenue = (
            float(row["Revenue (€)"])
            * revenue_multiplier
        )

        opex = (
            float(row["OPEX (€)"])
            * opex_multiplier
        )

        ebit = revenue - opex - depreciation

        tax = max(ebit, 0) * tax_rate

        fcf = ebit - tax + depreciation

        if t == final_year:
            fcf += working_capital

        discount_factor = 1 / ((1 + discount_rate) ** t)
        npv_value += fcf * discount_factor

    return npv_value


# ------------------------------------------------------------
# MODEL VALIDATION
# ------------------------------------------------------------

sensitivity_summary = tea_summary[
    tea_summary["Technology"] == sensitivity_technology
].iloc[0]

reported_baseline_npv = float(
    sensitivity_summary["NPV (€)"]
)

recalculated_baseline_npv = calculate_tea_npv_for_technology(
    sensitivity_technology
)

npv_validation_difference = (
    recalculated_baseline_npv - reported_baseline_npv
)

st.subheader("Baseline Model Validation (0% change)")

st.caption(
    "This check validates the deterministic baseline only. "
    "It is intentionally fixed at 0% parameter change and therefore does not "
    "change when the sensitivity interval is adjusted."
)

v1, v2, v3 = st.columns(3)

v1.metric(
    "Reported baseline NPV",
    f"€{reported_baseline_npv:,.0f}"
)

v2.metric(
    "Recalculated baseline NPV",
    f"€{recalculated_baseline_npv:,.0f}"
)

v3.metric(
    "Validation difference",
    f"€{npv_validation_difference:,.2f}"
)

if abs(npv_validation_difference) < 1.0:
    st.success(
        "Baseline validation passed: the recalculated NPV matches the reported NPV. "
        "Sensitivity results below are measured relative to this fixed baseline."
    )
else:
    st.warning(
        "Baseline validation difference is not negligible. Review the TEA cash-flow "
        "inputs before interpreting the sensitivity results."
    )

st.subheader("Current Sensitivity Test")

low_change = -sensitivity_range_pct
high_change = sensitivity_range_pct

s1, s2, s3, s4 = st.columns(4)

s1.metric(
    "Selected interval",
    f"±{sensitivity_range_pct}%"
)

s2.metric(
    "Lower test point",
    f"{low_change}%"
)

s3.metric(
    "Upper test point",
    f"+{high_change}%"
)

s4.metric(
    "Parameters selected",
    f"{len(selected_parameters)}"
)

st.info(
    "The sensitivity curves and tornado analysis below will test "
    f"{', '.join(selected_parameters)} over the interval "
    f"−{sensitivity_range_pct}% to +{sensitivity_range_pct}%, while all other "
    "inputs are held at their baseline values. For CO₂ Price Policy, the percentage "
    "change is referenced to the €50/tCO₂ baseline; a dedicated absolute-price policy "
    "threshold analysis is shown below when that lever is selected."
)


# ------------------------------------------------------------
# OAT SENSITIVITY FOR SELECTED TECHNOLOGY
# ------------------------------------------------------------

r = sensitivity_range_pct / 100

variation_levels = np.array([
    1 - r,
    1 - r / 2,
    1.0,
    1 + r / 2,
    1 + r,
])

sensitivity_results = []

for parameter in selected_parameters:
    for multiplier in variation_levels:
        npv_value = calculate_tea_npv_for_technology(
            sensitivity_technology,
            parameter=parameter,
            multiplier=float(multiplier)
        )

        sensitivity_results.append({
            "Parameter": parameter,
            "Input Change (%)": (multiplier - 1) * 100,
            "NPV (€)": npv_value,
        })

sensitivity_df = pd.DataFrame(sensitivity_results)


# ------------------------------------------------------------
# SENSITIVITY CURVES
# ------------------------------------------------------------

st.subheader("NPV Sensitivity Curves")

sensitivity_fig = px.line(
    sensitivity_df,
    x="Input Change (%)",
    y="NPV (€)",
    color="Parameter",
    markers=True,
    labels={
        "Input Change (%)": "Change in Input Parameter (%)",
        "NPV (€)": "NPV (€)",
        "Parameter": "",
    }
)

sensitivity_fig.add_hline(
    y=0,
    line_dash="dash",
    annotation_text="NPV = 0"
)

sensitivity_fig.update_layout(
    height=600,
    legend_title_text=""
)

st.plotly_chart(
    sensitivity_fig,
    use_container_width=True
)


# ------------------------------------------------------------
# TORNADO ANALYSIS
# ------------------------------------------------------------

st.subheader("Tornado Sensitivity Analysis")

tornado_rows = []

for parameter in selected_parameters:
    parameter_df = sensitivity_df[
        sensitivity_df["Parameter"] == parameter
    ].copy()

    low_change = -sensitivity_range_pct
    high_change = sensitivity_range_pct

    low_match = parameter_df.loc[
        np.isclose(
            parameter_df["Input Change (%)"],
            low_change
        ),
        "NPV (€)"
    ]

    high_match = parameter_df.loc[
        np.isclose(
            parameter_df["Input Change (%)"],
            high_change
        ),
        "NPV (€)"
    ]

    if low_match.empty or high_match.empty:
        continue

    npv_low = float(low_match.iloc[0])
    npv_high = float(high_match.iloc[0])

    sensitivity_span = abs(npv_high - npv_low)

    tornado_rows.append({
        "Parameter": parameter,
        "NPV Low": npv_low,
        "NPV High": npv_high,
        "Sensitivity Range": sensitivity_span,
    })

tornado_df = pd.DataFrame(tornado_rows)

tornado_df["Change at Low"] = (
    tornado_df["NPV Low"] - recalculated_baseline_npv
)

tornado_df["Change at High"] = (
    tornado_df["NPV High"] - recalculated_baseline_npv
)

tornado_df = tornado_df.sort_values(
    "Sensitivity Range",
    ascending=True
).reset_index(drop=True)

tornado_fig = go.Figure()

tornado_fig.add_trace(
    go.Bar(
        name=f"-{sensitivity_range_pct}% Input",
        y=tornado_df["Parameter"],
        x=tornado_df["Change at Low"],
        orientation="h",
        customdata=tornado_df[["NPV Low"]].to_numpy(),
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"Input change: -{sensitivity_range_pct}%<br>"
            "NPV: €%{customdata[0]:,.0f}<br>"
            "Change from baseline: €%{x:,.0f}"
            "<extra></extra>"
        )
    )
)

tornado_fig.add_trace(
    go.Bar(
        name=f"+{sensitivity_range_pct}% Input",
        y=tornado_df["Parameter"],
        x=tornado_df["Change at High"],
        orientation="h",
        customdata=tornado_df[["NPV High"]].to_numpy(),
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"Input change: +{sensitivity_range_pct}%<br>"
            "NPV: €%{customdata[0]:,.0f}<br>"
            "Change from baseline: €%{x:,.0f}"
            "<extra></extra>"
        )
    )
)

tornado_fig.add_vline(
    x=0,
    line_dash="dash",
    annotation_text="Baseline NPV",
    annotation_position="top"
)

tornado_fig.update_layout(
    barmode="overlay",
    height=max(450, 55 * len(tornado_df)),
    xaxis_title="Change in NPV relative to baseline (€)",
    yaxis_title="",
    legend_title_text="",
    hovermode="closest"
)

st.plotly_chart(
    tornado_fig,
    use_container_width=True
)


# ------------------------------------------------------------
# SENSITIVITY RANKING
# ------------------------------------------------------------

st.subheader("Sensitivity Ranking")

tornado_table = tornado_df.copy()

tornado_table["NPV Range (€)"] = tornado_table["Sensitivity Range"]

tornado_table = tornado_table[
    [
        "Parameter",
        "NPV Low",
        "NPV High",
        "NPV Range (€)",
    ]
].sort_values(
    "NPV Range (€)",
    ascending=False
).reset_index(drop=True)

tornado_table["Rank"] = range(1, len(tornado_table) + 1)

tornado_table = tornado_table[
    [
        "Rank",
        "Parameter",
        "NPV Low",
        "NPV High",
        "NPV Range (€)",
    ]
]

tornado_table = tornado_table.rename(
    columns={
        "NPV Low": f"NPV -{sensitivity_range_pct}%",
        "NPV High": f"NPV +{sensitivity_range_pct}%",
    }
)

st.dataframe(
    tornado_table,
    use_container_width=True,
    hide_index=True
)


# ------------------------------------------------------------
# DECISION-SWITCH ANALYSIS ACROSS ALL TECHNOLOGIES
# ------------------------------------------------------------

st.subheader("Decision-Switch Analysis")

st.caption(
    "For each selected parameter, the dashboard varies that parameter across "
    "the selected interval for every technology and checks whether the "
    "technology with the highest NPV changes. The reported threshold is the "
    "closest tested change to the baseline at which the winner changes."
)

technologies_sensitivity = sorted(
    tea_summary["Technology"].dropna().unique()
)

baseline_npv_by_technology = {
    technology: calculate_tea_npv_for_technology(technology)
    for technology in technologies_sensitivity
}

baseline_winner_sensitivity = max(
    baseline_npv_by_technology,
    key=baseline_npv_by_technology.get
)

# Fine grid for approximate switch threshold.
# 0.25 percentage-point resolution keeps the calculation responsive.
step_pct = 0.25
change_grid_pct = np.arange(
    -sensitivity_range_pct,
    sensitivity_range_pct + step_pct,
    step_pct
)

switch_rows = []

for parameter in selected_parameters:
    switch_candidates = []

    for change_pct in change_grid_pct:
        multiplier = 1 + change_pct / 100

        npv_by_technology = {
            technology: calculate_tea_npv_for_technology(
                technology,
                parameter=parameter,
                multiplier=multiplier
            )
            for technology in technologies_sensitivity
        }

        winner = max(
            npv_by_technology,
            key=npv_by_technology.get
        )

        if winner != baseline_winner_sensitivity:
            switch_candidates.append({
                "change_pct": float(change_pct),
                "winner": winner,
                "winner_npv": float(npv_by_technology[winner]),
                "baseline_winner_npv": float(
                    npv_by_technology[baseline_winner_sensitivity]
                ),
            })

    if switch_candidates:
        nearest_switch = min(
            switch_candidates,
            key=lambda x: abs(x["change_pct"])
        )

        switch_rows.append({
            "Parameter": parameter,
            "Decision Switch?": "Yes",
            "Approx. Switch Threshold (%)": nearest_switch["change_pct"],
            "New Winner": nearest_switch["winner"],
            "NPV Gap at Switch (€)": (
                nearest_switch["winner_npv"]
                - nearest_switch["baseline_winner_npv"]
            ),
        })

    else:
        switch_rows.append({
            "Parameter": parameter,
            "Decision Switch?": "No",
            "Approx. Switch Threshold (%)": np.nan,
            "New Winner": "—",
            "NPV Gap at Switch (€)": np.nan,
        })

switch_df = pd.DataFrame(switch_rows)

# Join influence magnitude so decision-critical and merely influential
# parameters can be distinguished.
switch_df = switch_df.merge(
    tornado_df[["Parameter", "Sensitivity Range"]],
    on="Parameter",
    how="left"
)

switch_df = switch_df.rename(
    columns={
        "Sensitivity Range": "NPV Sensitivity Range (€)"
    }
)

switch_df["Decision Priority"] = np.where(
    switch_df["Decision Switch?"] == "Yes",
    "Decision-critical",
    "Decision-stable"
)

switch_df = switch_df.sort_values(
    by=["Decision Switch?", "NPV Sensitivity Range (€)"],
    ascending=[False, False]
).reset_index(drop=True)

s1, s2, s3 = st.columns(3)

s1.metric(
    "Baseline Highest-NPV Technology",
    baseline_winner_sensitivity
)

n_switching = int(
    (switch_df["Decision Switch?"] == "Yes").sum()
)

s2.metric(
    "Decision-Critical Parameters",
    f"{n_switching} / {len(switch_df)}"
)

if n_switching > 0:
    nearest_overall = (
        switch_df[switch_df["Decision Switch?"] == "Yes"]
        .assign(
            Abs_Threshold=lambda x:
            x["Approx. Switch Threshold (%)"].abs()
        )
        .sort_values("Abs_Threshold")
        .iloc[0]
    )

    s3.metric(
        "Nearest Decision Switch",
        f"{nearest_overall['Approx. Switch Threshold (%)']:+.2f}%"
    )
    s3.caption(
        f"{nearest_overall['Parameter']} → {nearest_overall['New Winner']}"
    )
else:
    s3.metric(
        "Nearest Decision Switch",
        "None"
    )
    s3.caption(
        f"No ranking reversal within ±{sensitivity_range_pct}%"
    )

st.dataframe(
    switch_df,
    use_container_width=True,
    hide_index=True
)


# ------------------------------------------------------------
# CO₂ PRICE POLICY THRESHOLD FOR SFR
# ------------------------------------------------------------

if "CO₂ Price Policy" in selected_parameters:
    st.subheader("CO₂ Price Policy Threshold for SFR")

    st.caption(
        "This policy-specific analysis varies the CO₂ price in absolute €/tCO₂, "
        "holds the other deterministic TEA inputs at baseline, and identifies the "
        "first price at which SFR becomes the highest-NPV technology. The mapping "
        "is consistent with the CO₂-linked revenue proxy used in the original Monte Carlo model."
    )

    policy_c1, policy_c2 = st.columns(2)
    with policy_c1:
        co2_policy_max = st.number_input(
            "Maximum CO₂ price to test (€/tCO₂)",
            min_value=50.0,
            max_value=1000.0,
            value=200.0,
            step=10.0,
            key="co2_policy_max_eur_t"
        )
    with policy_c2:
        co2_policy_step = st.number_input(
            "CO₂ price resolution (€/tCO₂)",
            min_value=0.1,
            max_value=10.0,
            value=0.5,
            step=0.1,
            key="co2_policy_step_eur_t"
        )

    # Include the baseline price explicitly and search from €0/tCO₂ upward.
    co2_price_grid = np.arange(
        0.0,
        float(co2_policy_max) + float(co2_policy_step) / 2,
        float(co2_policy_step)
    )

    co2_policy_rows = []
    for co2_price in co2_price_grid:
        price_multiplier = co2_price / CO2_PRICE_BASE_EUR_T
        npv_by_technology = {}
        for technology in technologies_sensitivity:
            npv_by_technology[technology] = calculate_tea_npv_for_technology(
                technology,
                parameter="CO₂ Price Policy",
                multiplier=price_multiplier
            )

        winner = max(npv_by_technology, key=npv_by_technology.get)
        for technology, npv_value in npv_by_technology.items():
            co2_policy_rows.append({
                "CO₂ Price (€/tCO₂)": float(co2_price),
                "Technology": technology,
                "NPV (€)": float(npv_value),
                "Winner": technology == winner,
            })

    co2_policy_df = pd.DataFrame(co2_policy_rows)

    sfr_candidates = co2_policy_df[
        co2_policy_df["Technology"].map(_is_sfr_technology)
        & co2_policy_df["Winner"]
    ].copy()

    # Find the first tested price where SFR is the NPV winner.
    if not sfr_candidates.empty:
        sfr_switch_price = float(sfr_candidates["CO₂ Price (€/tCO₂)"].min())
        switch_slice = co2_policy_df[
            np.isclose(
                co2_policy_df["CO₂ Price (€/tCO₂)"],
                sfr_switch_price
            )
        ].sort_values("NPV (€)", ascending=False).reset_index(drop=True)

        sfr_switch_npv = float(switch_slice.iloc[0]["NPV (€)"])
        runner_up_name = switch_slice.iloc[1]["Technology"] if len(switch_slice) > 1 else "—"
        runner_up_npv = float(switch_slice.iloc[1]["NPV (€)"]) if len(switch_slice) > 1 else np.nan
        switch_margin = sfr_switch_npv - runner_up_npv if len(switch_slice) > 1 else np.nan

        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline CO₂ price", f"€{CO2_PRICE_BASE_EUR_T:,.0f}/tCO₂")
        m2.metric("SFR decision-switch price", f"≈ €{sfr_switch_price:,.1f}/tCO₂")
        m3.metric("NPV lead at switch", f"€{switch_margin:,.0f}")

        st.success(
            f"Policy decision rule: at a CO₂ price of approximately €{sfr_switch_price:,.1f}/tCO₂ "
            f"or higher, SFR becomes the highest-NPV option under the current deterministic assumptions. "
            f"At the switch point it overtakes {runner_up_name}."
        )
    else:
        sfr_switch_price = None
        st.warning(
            f"SFR does not become the highest-NPV option within the tested range of "
            f"€0–€{co2_policy_max:,.0f}/tCO₂. Increase the maximum CO₂ price to continue the search."
        )

    co2_policy_fig = px.line(
        co2_policy_df,
        x="CO₂ Price (€/tCO₂)",
        y="NPV (€)",
        color="Technology",
        labels={
            "CO₂ Price (€/tCO₂)": "CO₂ price (€/tCO₂)",
            "NPV (€)": "NPV (€)",
            "Technology": "Technology",
        },
    )
    co2_policy_fig.add_vline(
        x=CO2_PRICE_BASE_EUR_T,
        line_dash="dash",
        annotation_text="Baseline €50/tCO₂",
        annotation_position="top left"
    )
    if sfr_switch_price is not None:
        co2_policy_fig.add_vline(
            x=sfr_switch_price,
            line_dash="dot",
            annotation_text=f"SFR preferred ≈ €{sfr_switch_price:,.1f}/tCO₂",
            annotation_position="top right"
        )
    co2_policy_fig.add_hline(
        y=0,
        line_dash="dot",
        annotation_text="NPV = 0",
        annotation_position="bottom right"
    )
    co2_policy_fig.update_layout(
        height=540,
        hovermode="x unified",
        legend_title_text="Technology"
    )
    st.plotly_chart(co2_policy_fig, use_container_width=True)

    # Show a compact policy table around baseline and the switch threshold.
    policy_points = [0.0, CO2_PRICE_BASE_EUR_T]
    if sfr_switch_price is not None:
        policy_points.extend([
            max(0.0, sfr_switch_price - 10.0),
            sfr_switch_price,
            min(float(co2_policy_max), sfr_switch_price + 10.0),
        ])

    policy_summary_rows = []
    for target_price in sorted(set(round(float(x), 4) for x in policy_points)):
        nearest_price = float(
            co2_price_grid[np.argmin(np.abs(co2_price_grid - target_price))]
        )
        point_df = co2_policy_df[
            np.isclose(co2_policy_df["CO₂ Price (€/tCO₂)"], nearest_price)
        ].sort_values("NPV (€)", ascending=False).reset_index(drop=True)
        if point_df.empty:
            continue
        policy_summary_rows.append({
            "CO₂ Price (€/tCO₂)": nearest_price,
            "Preferred Technology": point_df.iloc[0]["Technology"],
            "Highest NPV (€)": point_df.iloc[0]["NPV (€)"],
            "Runner-up": point_df.iloc[1]["Technology"] if len(point_df) > 1 else "—",
            "NPV Lead (€)": (
                point_df.iloc[0]["NPV (€)"] - point_df.iloc[1]["NPV (€)"]
                if len(point_df) > 1 else np.nan
            ),
        })

    st.dataframe(
        pd.DataFrame(policy_summary_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "CO₂ Price (€/tCO₂)": st.column_config.NumberColumn(format="€ %.1f"),
            "Highest NPV (€)": st.column_config.NumberColumn(format="€ %.0f"),
            "NPV Lead (€)": st.column_config.NumberColumn(format="€ %.0f"),
        }
    )


# ------------------------------------------------------------
# TECHNOLOGY NPV COMPARISON ACROSS PARAMETER CHANGES
# ------------------------------------------------------------

st.subheader("Technology NPV Comparison Across Parameter Changes")
st.caption(
    "Instead of showing only the winning technology, this chart shows the NPV trajectory of all "
    "three technologies. A ranking switch occurs where the lines cross."
)

decision_curve_rows = []
plot_change_grid = np.linspace(
    -sensitivity_range_pct,
    sensitivity_range_pct,
    81
)

for parameter in selected_parameters:
    for change_pct in plot_change_grid:
        multiplier = 1 + change_pct / 100
        npv_by_technology = {
            technology: calculate_tea_npv_for_technology(
                technology,
                parameter=parameter,
                multiplier=multiplier
            )
            for technology in technologies_sensitivity
        }
        winner = max(npv_by_technology, key=npv_by_technology.get)

        for technology, npv_value in npv_by_technology.items():
            decision_curve_rows.append({
                "Parameter": parameter,
                "Input Change (%)": float(change_pct),
                "Technology": technology,
                "NPV (€)": float(npv_value),
                "Winner": technology == winner,
            })

decision_curve_df = pd.DataFrame(decision_curve_rows)

parameter_for_comparison = st.selectbox(
    "Parameter to inspect across all technologies",
    options=selected_parameters,
    index=0,
    key="decision_curve_parameter"
)

comparison_df = decision_curve_df[
    decision_curve_df["Parameter"] == parameter_for_comparison
].copy()

comparison_fig = px.line(
    comparison_df,
    x="Input Change (%)",
    y="NPV (€)",
    color="Technology",
    markers=False,
    labels={
        "Input Change (%)": "Change in selected parameter (%)",
        "NPV (€)": "NPV (€)",
        "Technology": "Technology",
    },
)
comparison_fig.add_vline(
    x=0,
    line_dash="dash",
    annotation_text="Baseline",
    annotation_position="top"
)
comparison_fig.add_hline(
    y=0,
    line_dash="dot",
    annotation_text="NPV = 0",
    annotation_position="bottom right"
)
comparison_fig.update_layout(
    height=520,
    legend_title_text="Technology",
    hovermode="x unified"
)
st.plotly_chart(comparison_fig, use_container_width=True)

# Compact winner summary at the lower bound, baseline and upper bound.
summary_points = [-sensitivity_range_pct, 0.0, sensitivity_range_pct]
comparison_summary_rows = []
for change_pct in summary_points:
    nearest_idx = (
        comparison_df["Input Change (%)"] - change_pct
    ).abs().idxmin()
    actual_change = float(comparison_df.loc[nearest_idx, "Input Change (%)"])
    point_df = comparison_df[
        np.isclose(comparison_df["Input Change (%)"], actual_change)
    ].copy()
    if point_df.empty:
        continue
    point_df = point_df.sort_values("NPV (€)", ascending=False).reset_index(drop=True)
    comparison_summary_rows.append({
        "Scenario": (
            "Baseline" if abs(change_pct) < 1e-9
            else f"{change_pct:+.0f}%"
        ),
        "Winner": point_df.iloc[0]["Technology"],
        "Winner NPV (€)": point_df.iloc[0]["NPV (€)"],
        "Runner-up": point_df.iloc[1]["Technology"] if len(point_df) > 1 else "—",
        "NPV lead (€)": (
            point_df.iloc[0]["NPV (€)"] - point_df.iloc[1]["NPV (€)"]
            if len(point_df) > 1 else np.nan
        ),
    })

comparison_summary_df = pd.DataFrame(comparison_summary_rows)
st.dataframe(
    comparison_summary_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Winner NPV (€)": st.column_config.NumberColumn(format="€ %.0f"),
        "NPV lead (€)": st.column_config.NumberColumn(format="€ %.0f"),
    }
)

if parameter_for_comparison in set(switch_df["Parameter"]):
    selected_switch_row = switch_df[
        switch_df["Parameter"] == parameter_for_comparison
    ].iloc[0]
    if selected_switch_row["Decision Switch?"] == "Yes":
        st.warning(
            f"Ranking switch detected for {parameter_for_comparison}: approximately "
            f"{selected_switch_row['Approx. Switch Threshold (%)']:+.2f}% changes the NPV winner to "
            f"{selected_switch_row['New Winner']}."
        )
    else:
        st.info(
            f"No NPV winner switch for {parameter_for_comparison} within "
            f"±{sensitivity_range_pct}%. The chart still shows how close the alternatives become."
        )

# ------------------------------------------------------------
# INTERPRETATION
# ------------------------------------------------------------

most_sensitive_parameter = tornado_table.iloc[0]

st.subheader("Sensitivity Interpretation")

st.info(
    f"For {sensitivity_technology}, "
    f"{most_sensitive_parameter['Parameter']} is currently the most "
    f"influential of the selected parameters, producing an NPV range of "
    f"approximately €{most_sensitive_parameter['NPV Range (€)']:,.0f} "
    f"across the ±{sensitivity_range_pct}% interval."
)

if n_switching > 0:
    nearest_overall = (
        switch_df[switch_df["Decision Switch?"] == "Yes"]
        .assign(
            Abs_Threshold=lambda x:
            x["Approx. Switch Threshold (%)"].abs()
        )
        .sort_values("Abs_Threshold")
        .iloc[0]
    )

    st.warning(
        f"Decision switch detected: changing "
        f"{nearest_overall['Parameter']} by approximately "
        f"{nearest_overall['Approx. Switch Threshold (%)']:+.2f}% "
        f"changes the highest-NPV technology from "
        f"{baseline_winner_sensitivity} to "
        f"{nearest_overall['New Winner']}."
    )
else:
    st.success(
        f"The highest-NPV technology ({baseline_winner_sensitivity}) remains "
        f"stable for all selected parameters within the tested "
        f"±{sensitivity_range_pct}% interval."
    )

st.caption(
    "This remains a deterministic OAT analysis. A parameter can have a large "
    "NPV effect without changing the preferred technology. Conversely, a "
    "smaller NPV effect can be decision-critical if competing alternatives "
    "are close. The Monte Carlo module below addresses the probability of "
    "such changes under simultaneous uncertainty."
)

# ============================================================
# MODULE 6 — MONTE CARLO UNCERTAINTY ANALYSIS
# ============================================================

st.divider()
st.header("Monte Carlo Uncertainty Analysis")
st.caption(
    "Source-based stochastic TEA model reconstructed from the original Monte Carlo code. "
    "At the default settings (N=10,000, seed=42, uncertainty scale=100%), the model should "
    "reproduce the original finding that Dual-Fuel is the most frequent NPV winner under uncertainty, "
    "even though Oxy-Enriched has the highest deterministic NPV."
)

# ------------------------------------------------------------
# SIMULATION SETTINGS
# ------------------------------------------------------------

st.subheader("Simulation Settings")
mc_col1, mc_col2, mc_col3 = st.columns(3)
with mc_col1:
    mc_simulations = st.number_input(
        "Number of Monte Carlo simulations",
        min_value=1000,
        max_value=50000,
        value=10000,
        step=1000,
        key="mc_simulations_reference"
    )
with mc_col2:
    mc_seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=999999,
        value=42,
        step=1,
        key="mc_seed_reference"
    )
with mc_col3:
    uncertainty_scale = st.slider(
        "Overall uncertainty scale (%)",
        min_value=0,
        max_value=200,
        value=100,
        step=5,
        key="mc_uncertainty_scale_reference",
        help=(
            "100% reproduces the original uncertainty ranges. 0% fixes stochastic inputs at their "
            "baseline/mode values. Values above 100% widen all uncertainty ranges proportionally."
        )
    )

st.info(
    f"Current run: {int(mc_simulations):,} simulations | seed {int(mc_seed)} | "
    f"uncertainty scale {uncertainty_scale}%"
)
st.caption(
    "Changing the number of simulations mainly changes sampling precision. Changing the uncertainty "
    "scale or the parameter assumptions below changes the simulated distributions and can change "
    "P(NPV > 0) and P(best NPV)."
)

# ------------------------------------------------------------
# SOURCE-BASED PARAMETER ASSUMPTIONS
# ------------------------------------------------------------

st.subheader("Stochastic Parameter Assumptions")
st.caption(
    "Defaults reproduce the assumptions in the original Monte Carlo model. Expand the panel to test "
    "alternative uncertainty assumptions."
)

with st.expander("Edit Monte Carlo parameters", expanded=False):
    p1, p2 = st.columns(2)
    with p1:
        el_unc_pct = st.slider("Electricity selling price uncertainty (±%)", 0, 60, 30, 1, key="mc_el_unc")
        methane_unc_pct = st.slider("Methane concentration / energy-yield uncertainty (±%)", 0, 50, 20, 1, key="mc_methane_unc")
        heat_util_range = st.slider("Heat utilisation range (%)", 0, 100, (40, 90), 1, key="mc_heat_util")
        capex_sd_pct = st.slider("CAPEX standard deviation (%)", 0, 30, 10, 1, key="mc_capex_sd")
        biodiesel_cv_pct = st.slider("Dual-Fuel biodiesel-price CV (%)", 0, 60, 25, 1, key="mc_bio_cv")
        pilot_sd_pct = st.slider("Dual-Fuel pilot-ratio SD (%)", 0, 30, 10, 1, key="mc_pilot_sd")
    with p2:
        discount_min_pct = st.slider("Discount-rate minimum (%)", 0.0, 15.0, 5.0, 0.5, key="mc_disc_min")
        discount_mode_pct = st.slider("Discount-rate mode (%)", 0.0, 20.0, 8.0, 0.5, key="mc_disc_mode")
        discount_max_pct = st.slider("Discount-rate maximum (%)", 0.0, 25.0, 12.0, 0.5, key="mc_disc_max")
        psa_sd = st.slider("OEC PSA electricity intensity SD (kWh/Nm³ O₂)", 0.0, 0.40, 0.13, 0.01, key="mc_psa_sd")
        co2_price_range = st.slider("SFR CO₂ selling-price range (€/t CO₂)", 0, 150, (30, 70), 5, key="mc_co2_price")
        capture_sd_pct = st.slider("SFR CO₂ capture-efficiency SD (percentage points)", 0.0, 15.0, 4.0, 0.5, key="mc_capture_sd")

    st.caption(
        "Additional source-model assumptions kept fixed in this demo: PSA grid-price triangular "
        "0.15/0.25/0.40 €/kWh; MEA price triangular 2.9/3.5/10 €/kg; solvent make-up 1.5% ±0.5%; "
        "tax rate 25%; working capital 5% of year-1 revenue."
    )

# Validate discount triangle before simulation.
if not (discount_min_pct <= discount_mode_pct <= discount_max_pct):
    st.error("Discount-rate inputs must satisfy minimum ≤ mode ≤ maximum.")
    st.stop()

# ------------------------------------------------------------
# REFERENCE CASH-FLOW SERIES FROM ORIGINAL MC MODEL
# ------------------------------------------------------------

rev_df_ref = np.array([
    2151318, 2047207, 1946987, 1851632, 1762116,
    1675518, 1593785, 1515945, 1441996, 1371940,
    1304802, 1241557, 1181230, 1122850, 1068362,
    1016792, 966780, 919686, 874831, 832116
], dtype=float)
rev_oxy_ref = np.array([
    1931009, 1837559, 1747602, 1662013, 1581663,
    1503933, 1430511, 1360622, 1294251, 1231374,
    1171122, 1114353, 1060265, 1007879, 958924,
    912646, 867765, 825679, 785242, 746789
], dtype=float)
rev_sfr_ref = np.array([
    1726852, 1642971, 1562746, 1486627, 1414537,
    1345324, 1279514, 1217088, 1157413, 1101409,
    1047538, 996768, 948491, 902055, 857748,
    815988, 776152, 738450, 702540, 668130
], dtype=float)

opex_df_ref = np.array([
    1380110, 1311479, 1246182, 1184670, 1127382,
    1072625, 1021385, 973055, 927563, 884842,
    844314, 806435, 770638, 736379, 704609,
    674781, 646170, 619423, 594166, 570315
], dtype=float)
opex_oxy_ref = np.array([
    1219221, 1161059, 1105773, 1053734, 1005298,
    959046, 915765, 874993, 836657, 800682,
    766586, 734734, 704687, 675937, 649263,
    624263, 600306, 578005, 556802, 536821
], dtype=float)
opex_sfr_ref = np.array([
    1146954, 1092826, 1041657, 993607, 948551,
    905804, 865579, 827800, 792078, 758827,
    727211, 697670, 669851, 643392, 618399,
    595037, 572969, 552261, 532722, 514186
], dtype=float)

CAPEX_DF_REF = 3009935.0
CAPEX_OXY_REF = 3080997.0
CAPEX_SFR_REF = 3115350.0
TAX_RATE_REF = 0.25
WC_PCT_REF = 0.05
PROJECT_LIFE_REF = 20

# ------------------------------------------------------------
# MONTE CARLO HELPERS
# ------------------------------------------------------------

rng_mc = np.random.default_rng(int(mc_seed))
n_mc = int(mc_simulations)
scale_u = float(uncertainty_scale) / 100.0


def _triangular_scaled(center, low, high, n):
    if scale_u == 0:
        return np.full(n, center, dtype=float)
    lo = center + (low - center) * scale_u
    hi = center + (high - center) * scale_u
    if lo > hi:
        lo, hi = hi, lo
    return rng_mc.triangular(lo, center, hi, n)


def _uniform_scaled(center, low, high, n):
    if scale_u == 0:
        return np.full(n, center, dtype=float)
    lo = center + (low - center) * scale_u
    hi = center + (high - center) * scale_u
    if lo > hi:
        lo, hi = hi, lo
    return rng_mc.uniform(lo, hi, n)


def _normal_scaled(mean, sd, n):
    if scale_u == 0 or sd == 0:
        return np.full(n, mean, dtype=float)
    return rng_mc.normal(mean, sd * scale_u, n)


def _beta_from_mean_sd_scaled(mean, sd, n):
    sd_eff = sd * scale_u
    if sd_eff <= 0:
        return np.full(n, mean, dtype=float)
    max_sd = np.sqrt(mean * (1 - mean)) * 0.999
    sd_eff = min(sd_eff, max_sd)
    var = sd_eff ** 2
    k = mean * (1 - mean) / var - 1
    alpha = max(mean * k, 1e-6)
    beta = max((1 - mean) * k, 1e-6)
    return rng_mc.beta(alpha, beta, n)


def _lognormal_from_mean_cv_scaled(mean, cv, n):
    cv_eff = cv * scale_u
    if cv_eff <= 0:
        return np.full(n, mean, dtype=float)
    sigma2 = np.log(1 + cv_eff ** 2)
    sigma = np.sqrt(sigma2)
    mu = np.log(mean) - 0.5 * sigma2
    return rng_mc.lognormal(mu, sigma, n)


def compute_npv_vectorized(rev_base, opex_base, capex, discount_rate, scale_rev, scale_opex):
    """Vectorized post-tax unlevered NPV with working-capital recovery."""
    n = len(capex)
    dep = capex / PROJECT_LIFE_REF
    wc = WC_PCT_REF * (rev_base[0] * scale_rev)
    npv = -(capex + wc)

    for year_idx in range(PROJECT_LIFE_REF):
        t_year = year_idx + 1
        revenue = rev_base[year_idx] * scale_rev
        opex = opex_base[year_idx] * scale_opex
        ebit = revenue - opex - dep
        tax = np.maximum(ebit, 0.0) * TAX_RATE_REF
        fcf = ebit - tax + dep
        if year_idx == PROJECT_LIFE_REF - 1:
            fcf = fcf + wc
        npv = npv + fcf / np.power(1.0 + discount_rate, t_year)
    return npv

# ------------------------------------------------------------
# SAMPLE ORIGINAL STOCHASTIC DRIVERS
# ------------------------------------------------------------

# Common variables
el_width = (el_unc_pct / 100.0)
sell_el = _triangular_scaled(0.12, 0.12 * (1 - el_width), 0.12 * (1 + el_width), n_mc)
heat_lo, heat_hi = heat_util_range
heat_center = (heat_lo + heat_hi) / 200.0
heat_util = _uniform_scaled(heat_center, heat_lo / 100.0, heat_hi / 100.0, n_mc)
meth_width = methane_unc_pct / 100.0
methane_factor = _uniform_scaled(1.0, 1.0 - meth_width, 1.0 + meth_width, n_mc)
discount_rate = _triangular_scaled(
    discount_mode_pct / 100.0,
    discount_min_pct / 100.0,
    discount_max_pct / 100.0,
    n_mc
)

# CAPEX draws are technology-specific, as in the original code.
capex_df_draw = np.clip(
    _normal_scaled(CAPEX_DF_REF, (capex_sd_pct / 100.0) * CAPEX_DF_REF, n_mc),
    0.5 * CAPEX_DF_REF,
    2.0 * CAPEX_DF_REF
)
capex_oxy_draw = np.clip(
    _normal_scaled(CAPEX_OXY_REF, (capex_sd_pct / 100.0) * CAPEX_OXY_REF, n_mc),
    0.5 * CAPEX_OXY_REF,
    2.0 * CAPEX_OXY_REF
)
capex_sfr_draw = np.clip(
    _normal_scaled(CAPEX_SFR_REF, (capex_sd_pct / 100.0) * CAPEX_SFR_REF, n_mc),
    0.5 * CAPEX_SFR_REF,
    2.0 * CAPEX_SFR_REF
)

# Dual-Fuel drivers
bio = _lognormal_from_mean_cv_scaled(1.0, biodiesel_cv_pct / 100.0, n_mc)
pilot = np.clip(_normal_scaled(1.0, pilot_sd_pct / 100.0, n_mc), 0.5, 1.5)

# OEC drivers
psa = np.clip(_normal_scaled(0.85, psa_sd, n_mc), 0.1, 2.0)
pgrid = _triangular_scaled(0.25, 0.15, 0.40, n_mc)

# SFR drivers
mea_price = _triangular_scaled(3.5, 2.9, 10.0, n_mc)
solv_mk = np.clip(_normal_scaled(0.015, 0.005, n_mc), 0.001, 0.05)
co2_low, co2_high = co2_price_range
co2_price = _triangular_scaled(50.0, float(co2_low), float(co2_high), n_mc)
eta = np.clip(_beta_from_mean_sd_scaled(0.85, capture_sd_pct / 100.0, n_mc), 0.5, 0.99)

# ------------------------------------------------------------
# TECHNOLOGY-SPECIFIC MAPPING FROM ORIGINAL MC MODEL
# ------------------------------------------------------------

base_sell = 0.12
w_heat_df, w_heat_oxy, w_heat_sfr = 0.35, 0.35, 0.05


def revenue_scale(w_heat):
    return methane_factor * ((1 - w_heat) + w_heat * heat_util) * (sell_el / base_sell)

scale_rev_df = revenue_scale(w_heat_df)
scale_rev_oxy = revenue_scale(w_heat_oxy)
scale_rev_sfr = revenue_scale(w_heat_sfr)

scale_opex_df = 0.7 + 0.3 * bio * pilot
scale_opex_oxy = 0.7 + 0.3 * (psa / 0.85) * (pgrid / 0.25)
scale_opex_sfr = (
    0.6
    + 0.2 * (mea_price / 3.5) * (solv_mk / 0.015)
    + 0.2 * (eta / 0.85)
)
co2_rev_factor = (co2_price / 50.0) * (eta / 0.85)
scale_rev_sfr = scale_rev_sfr * (0.7 + 0.3 * co2_rev_factor)

# Calculate NPV arrays.
npv_df_mc = compute_npv_vectorized(
    rev_df_ref, opex_df_ref, capex_df_draw, discount_rate, scale_rev_df, scale_opex_df
)
npv_oxy_mc = compute_npv_vectorized(
    rev_oxy_ref, opex_oxy_ref, capex_oxy_draw, discount_rate, scale_rev_oxy, scale_opex_oxy
)
npv_sfr_mc = compute_npv_vectorized(
    rev_sfr_ref, opex_sfr_ref, capex_sfr_draw, discount_rate, scale_rev_sfr, scale_opex_sfr
)

# Resolve dashboard technology labels dynamically so this module remains compatible
# with the processed CSV naming convention.
def _find_tech_label(kind):
    names = tea_summary["Technology"].dropna().astype(str).tolist()
    if kind == "df":
        candidates = [x for x in names if "dual" in x.lower() or x.strip().lower() in {"df", "dfc"}]
    elif kind == "oxy":
        candidates = [x for x in names if "oxy" in x.lower() or "oxygen" in x.lower() or x.strip().lower() == "oec"]
    else:
        candidates = [x for x in names if "sfr" in x.lower()]
    return candidates[0] if candidates else {"df": "Dual-Fuel", "oxy": "Oxy-Enriched", "sfr": "SFR+CO2"}[kind]

tech_df_label = _find_tech_label("df")
tech_oxy_label = _find_tech_label("oxy")
tech_sfr_label = _find_tech_label("sfr")
technologies_mc = [tech_df_label, tech_oxy_label, tech_sfr_label]

mc_results = pd.concat([
    pd.DataFrame({"Technology": tech_df_label, "Simulation": np.arange(1, n_mc + 1), "NPV (€)": npv_df_mc}),
    pd.DataFrame({"Technology": tech_oxy_label, "Simulation": np.arange(1, n_mc + 1), "NPV (€)": npv_oxy_mc}),
    pd.DataFrame({"Technology": tech_sfr_label, "Simulation": np.arange(1, n_mc + 1), "NPV (€)": npv_sfr_mc}),
], ignore_index=True)

ranking_wide = pd.DataFrame({
    tech_df_label: npv_df_mc,
    tech_oxy_label: npv_oxy_mc,
    tech_sfr_label: npv_sfr_mc,
}, index=np.arange(1, n_mc + 1))
ranking_wide.index.name = "Simulation"

# ------------------------------------------------------------
# REFERENCE BENCHMARK CHECK
# ------------------------------------------------------------

st.subheader("Reference Monte Carlo Benchmark")
reference_benchmark = pd.DataFrame({
    "Technology": [tech_df_label, tech_oxy_label, tech_sfr_label],
    "Reference P(NPV > 0) (%)": [46.13, 35.78, 33.01],
    "Reference P(best NPV) (%)": [54.48, 19.83, 25.69],
})

winner_each_simulation = ranking_wide.idxmax(axis=1)
ranking_probability = (
    winner_each_simulation.value_counts(normalize=True)
    .mul(100)
    .reindex(technologies_mc, fill_value=0.0)
    .rename_axis("Technology")
    .reset_index(name="P(best NPV) (%)")
)

comparison_mc = (
    mc_results.groupby("Technology")["NPV (€)"]
    .agg(
        Mean_NPV="mean",
        Median_NPV="median",
        Std_NPV="std",
        P05=lambda x: x.quantile(0.05),
        P95=lambda x: x.quantile(0.95),
        Probability_Positive_NPV=lambda x: (x > 0).mean() * 100,
    )
    .reset_index()
    .rename(columns={
        "Mean_NPV": "Mean NPV (€)",
        "Median_NPV": "Median NPV (€)",
        "Std_NPV": "Standard Deviation (€)",
        "Probability_Positive_NPV": "P(NPV > 0) (%)",
    })
)
comparison_mc = comparison_mc.merge(ranking_probability, on="Technology", how="left")
benchmark_check = comparison_mc.merge(reference_benchmark, on="Technology", how="left")
benchmark_check["Δ P(NPV > 0) (pp)"] = benchmark_check["P(NPV > 0) (%)"] - benchmark_check["Reference P(NPV > 0) (%)"]
benchmark_check["Δ P(best) (pp)"] = benchmark_check["P(best NPV) (%)"] - benchmark_check["Reference P(best NPV) (%)"]

st.dataframe(
    benchmark_check[[
        "Technology", "P(NPV > 0) (%)", "Reference P(NPV > 0) (%)",
        "P(best NPV) (%)", "Reference P(best NPV) (%)",
        "Δ P(NPV > 0) (pp)", "Δ P(best) (pp)"
    ]],
    use_container_width=True,
    hide_index=True
)

if int(mc_seed) == 42 and int(mc_simulations) == 10000 and uncertainty_scale == 100:
    st.success(
        "Reference configuration active. Small differences from the archived Excel benchmark are expected "
        "because the archived raw run may come from a nearby code revision, but Dual-Fuel should remain "
        "the most frequent NPV winner."
    )
else:
    st.caption(
        "The reference columns are shown only as a benchmark. Once you change N, seed, uncertainty scale, "
        "or parameter assumptions, the current simulation is intentionally a different scenario."
    )

# ------------------------------------------------------------
# NPV DISTRIBUTION
# ------------------------------------------------------------

st.subheader("NPV Uncertainty Distribution")
selected_mc_technology = st.selectbox(
    "Technology",
    technologies_mc,
    key="mc_technology_reference"
)
selected_mc_df = mc_results[mc_results["Technology"] == selected_mc_technology].copy()

mc_mean = selected_mc_df["NPV (€)"].mean()
mc_median = selected_mc_df["NPV (€)"].median()
mc_std = selected_mc_df["NPV (€)"].std()
mc_p05 = selected_mc_df["NPV (€)"].quantile(0.05)
mc_p50 = selected_mc_df["NPV (€)"].quantile(0.50)
mc_p95 = selected_mc_df["NPV (€)"].quantile(0.95)
prob_positive_npv = (selected_mc_df["NPV (€)"] > 0).mean() * 100

m1, m2, m3, m4 = st.columns(4)
m1.metric("Mean NPV", f"€{mc_mean:,.0f}")
m2.metric("Median NPV", f"€{mc_median:,.0f}")
m3.metric("P(NPV > 0)", f"{prob_positive_npv:.1f}%")
m4.metric("Standard Deviation", f"€{mc_std:,.0f}")

mc_histogram = px.histogram(
    selected_mc_df,
    x="NPV (€)",
    nbins=60,
    labels={"NPV (€)": "Net Present Value (€)"}
)
mc_histogram.add_vline(x=0, line_dash="dash", annotation_text="NPV = 0")
mc_histogram.add_vline(x=mc_p50, line_dash="dot", annotation_text="Median")
mc_histogram.update_layout(height=500, yaxis_title="Frequency")
st.plotly_chart(mc_histogram, use_container_width=True)

st.subheader("NPV Risk Percentiles")
p1, p2, p3 = st.columns(3)
p1.metric("P05", f"€{mc_p05:,.0f}")
p2.metric("P50", f"€{mc_p50:,.0f}")
p3.metric("P95", f"€{mc_p95:,.0f}")

# ------------------------------------------------------------
# CROSS-TECHNOLOGY COMPARISON
# ------------------------------------------------------------

st.subheader("Probabilistic Technology Comparison")
st.dataframe(
    comparison_mc.sort_values("P(best NPV) (%)", ascending=False),
    use_container_width=True,
    hide_index=True
)

# ------------------------------------------------------------
# ECONOMIC RANKING ROBUSTNESS
# ------------------------------------------------------------

st.subheader("Economic Ranking Robustness")
ranking_probability = ranking_probability.sort_values("P(best NPV) (%)", ascending=False)
ranking_fig = px.bar(
    ranking_probability,
    x="Technology",
    y="P(best NPV) (%)",
    text="P(best NPV) (%)",
    labels={"P(best NPV) (%)": "Probability of Highest NPV (%)"}
)
ranking_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
ranking_fig.update_layout(height=450, yaxis_range=[0, 100])
st.plotly_chart(ranking_fig, use_container_width=True)
st.dataframe(ranking_probability, use_container_width=True, hide_index=True)

most_economic_robust = ranking_probability.iloc[0]
deterministic_winner = tea_summary.loc[tea_summary["NPV (€)"].idxmax(), "Technology"]

if most_economic_robust["Technology"] != deterministic_winner:
    st.warning(
        f"Decision reversal under uncertainty: deterministic TEA favours {deterministic_winner}, "
        f"but {most_economic_robust['Technology']} achieves the highest NPV in "
        f"{most_economic_robust['P(best NPV) (%)']:.1f}% of Monte Carlo simulations."
    )
else:
    st.info(
        f"{most_economic_robust['Technology']} is both the deterministic NPV winner and the most frequent "
        f"probabilistic NPV winner ({most_economic_robust['P(best NPV) (%)']:.1f}%)."
    )

st.caption(
    "This is an economic ranking only. The integrated LCA–TEA decision module below combines these "
    "probabilistic economic outcomes with environmental performance."
)

# Generic helper retained for Module 7 environmental Monte Carlo.
def triangular_multipliers(rng, uncertainty_pct, n):
    if uncertainty_pct <= 0:
        return np.ones(n, dtype=float)
    width = uncertainty_pct / 100.0
    return rng.triangular(1.0 - width, 1.0, 1.0 + width, size=n)

# MODULE 7 — MULTI-IMPACT LCA–TEA DECISION ROBUSTNESS
# ============================================================

st.divider()
st.header("Multi-Impact LCA–TEA Decision Robustness")
st.caption(
    "This demo combines multiple normalized LCIA midpoint categories with probabilistic TEA results. "
    "Each selected environmental category is normalized across the competing technologies before "
    "aggregation, preventing categories with large numerical units from dominating only because of scale."
)

# ------------------------------------------------------------
# DECISION SETTINGS
# ------------------------------------------------------------

st.subheader("Integrated Decision Settings")

all_integrated_impacts = sorted(master_df["Impact category"].dropna().unique())

# For a public demo, use all available LCIA categories by default. The user can
# deselect categories to test how the decision depends on environmental scope.
default_impacts = all_integrated_impacts.copy()

selected_integrated_impacts = st.multiselect(
    "Environmental impact categories included in the decision",
    options=all_integrated_impacts,
    default=default_impacts,
    key="multiimpact_categories_final",
)

if not selected_integrated_impacts:
    st.warning("Select at least one environmental impact category to continue the integrated analysis.")
    st.stop()

set_col1, set_col2 = st.columns(2)

with set_col1:
    environmental_weight_pct = st.slider(
        "Overall environmental weight (%)",
        min_value=0,
        max_value=100,
        value=50,
        step=5,
        key="multiimpact_environmental_weight_final",
    )

with set_col2:
    lcia_uncertainty = st.slider(
        "LCIA uncertainty (%)",
        min_value=0,
        max_value=50,
        value=0,
        step=1,
        key="multiimpact_lcia_uncertainty_final",
    )

economic_weight_pct = 100 - environmental_weight_pct

weighting_mode = st.radio(
    "Weighting among selected environmental categories",
    options=["Equal weighting", "Custom weighting"],
    horizontal=True,
    key="multiimpact_weighting_mode_final",
)

# ------------------------------------------------------------
# CATEGORY WEIGHTS
# ------------------------------------------------------------

if weighting_mode == "Equal weighting":
    category_weight_map = {
        impact: 1.0 / len(selected_integrated_impacts)
        for impact in selected_integrated_impacts
    }
else:
    st.caption(
        "Enter relative weights. They do not need to sum to 100; the dashboard normalizes them automatically."
    )
    custom_weight_rows = []
    n_cols = 2
    cols = st.columns(n_cols)
    for idx, impact in enumerate(selected_integrated_impacts):
        with cols[idx % n_cols]:
            raw_weight = st.number_input(
                impact,
                min_value=0.0,
                max_value=1000.0,
                value=1.0,
                step=0.1,
                key=f"impact_weight_final_{idx}_{impact}",
            )
        custom_weight_rows.append((impact, float(raw_weight)))

    raw_total = sum(v for _, v in custom_weight_rows)
    if raw_total <= 0:
        st.error("At least one environmental category weight must be greater than zero.")
        st.stop()
    category_weight_map = {k: v / raw_total for k, v in custom_weight_rows}

st.info(
    f"Current decision weighting: Environmental {environmental_weight_pct}% | "
    f"Economic {economic_weight_pct}%. Environmental sub-weights are "
    f"{'equal across selected categories' if weighting_mode == 'Equal weighting' else 'user-defined and normalized'}."
)

# ------------------------------------------------------------
# PREPARE MULTI-IMPACT LCA MATRIX
# ------------------------------------------------------------

lca_decision = master_df[
    master_df["Impact category"].isin(selected_integrated_impacts)
][["Technology", "Impact category", "Result", "Reference unit"]].copy()

lca_decision = lca_decision[
    lca_decision["Technology"].isin(technologies_mc)
].copy()

# Average duplicate rows if present, preserving one reference unit per category.
lca_decision = (
    lca_decision.groupby(["Technology", "Impact category"], as_index=False)
    .agg({"Result": "mean", "Reference unit": "first"})
)

coverage = (
    lca_decision.groupby("Technology")["Impact category"].nunique()
)
common_technologies = [
    tech for tech in technologies_mc
    if coverage.get(tech, 0) == len(selected_integrated_impacts)
]

if len(common_technologies) < 2:
    st.error(
        "Fewer than two technologies contain complete results for all selected LCIA categories. "
        "Reduce the selected categories or check the processed LCA data."
    )
    st.stop()

lca_decision = lca_decision[
    lca_decision["Technology"].isin(common_technologies)
].copy()

# ------------------------------------------------------------
# BASELINE NORMALIZED ENVIRONMENTAL SCORES BY CATEGORY
# Lower impact = better. Each category is min-max normalized across alternatives.
# ------------------------------------------------------------

env_score_rows = []
category_diagnostics = []

for impact in selected_integrated_impacts:
    category_df = lca_decision[
        lca_decision["Impact category"] == impact
    ].copy()

    values = category_df.set_index("Technology")["Result"].reindex(common_technologies)
    vmin = float(values.min())
    vmax = float(values.max())
    vrange = vmax - vmin

    if np.isclose(vrange, 0.0):
        scores = pd.Series(0.5, index=values.index)
    else:
        scores = (vmax - values) / vrange

    cat_weight = float(category_weight_map[impact])

    for tech in common_technologies:
        env_score_rows.append({
            "Technology": tech,
            "Impact category": impact,
            "Raw LCIA Result": float(values.loc[tech]),
            "Normalized Environmental Score": float(scores.loc[tech]),
            "Category Weight": cat_weight,
            "Weighted Environmental Score": float(scores.loc[tech]) * cat_weight,
        })

    category_diagnostics.append({
        "Impact category": impact,
        "Weight (%)": cat_weight * 100,
        "Best technology": str(values.idxmin()),
        "Worst technology": str(values.idxmax()),
        "Best result": vmin,
        "Worst result": vmax,
    })

env_scores_long = pd.DataFrame(env_score_rows)
category_diagnostics_df = pd.DataFrame(category_diagnostics)

environmental_composite = (
    env_scores_long.groupby("Technology", as_index=False)["Weighted Environmental Score"]
    .sum()
    .rename(columns={"Weighted Environmental Score": "Composite Environmental Score"})
)

environmental_composite = environmental_composite.sort_values(
    "Composite Environmental Score", ascending=False
).reset_index(drop=True)
environmental_composite["Environmental Rank"] = np.arange(1, len(environmental_composite) + 1)

st.subheader("Multi-Impact Environmental Ranking")

env_rank_display = environmental_composite[[
    "Environmental Rank", "Technology", "Composite Environmental Score"
]].copy()
st.dataframe(env_rank_display, use_container_width=True, hide_index=True)

with st.expander("Environmental category diagnostics and normalized contributions"):
    st.dataframe(category_diagnostics_df, use_container_width=True, hide_index=True)

    env_contrib_display = env_scores_long.copy()
    st.dataframe(env_contrib_display, use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# BASELINE ECONOMIC + INTEGRATED SCORES
# ------------------------------------------------------------

# Use the deterministic TEA summary as the baseline economic source.
# Module 7 must not depend on the temporary validation dataframe from Module 5.
baseline_integrated = tea_summary[
    tea_summary["Technology"].isin(common_technologies)
][["Technology", "NPV (€)"]].copy()
baseline_integrated = baseline_integrated.rename(
    columns={"NPV (€)": "Recalculated NPV (€)"}
)

baseline_integrated = baseline_integrated.merge(
    environmental_composite[["Technology", "Composite Environmental Score"]],
    on="Technology",
    how="inner",
)

base_npv_min = float(baseline_integrated["Recalculated NPV (€)"].min())
base_npv_max = float(baseline_integrated["Recalculated NPV (€)"].max())
base_npv_range = base_npv_max - base_npv_min

if np.isclose(base_npv_range, 0.0):
    baseline_integrated["Economic Score"] = 0.5
else:
    baseline_integrated["Economic Score"] = (
        (baseline_integrated["Recalculated NPV (€)"] - base_npv_min)
        / base_npv_range
    )

w_env = environmental_weight_pct / 100.0
w_eco = economic_weight_pct / 100.0

baseline_integrated["Integrated Score"] = (
    w_env * baseline_integrated["Composite Environmental Score"]
    + w_eco * baseline_integrated["Economic Score"]
)

baseline_integrated = baseline_integrated.sort_values(
    "Integrated Score", ascending=False
).reset_index(drop=True)
baseline_integrated["Rank"] = np.arange(1, len(baseline_integrated) + 1)

baseline_integrated_winner = baseline_integrated.iloc[0]["Technology"]

st.subheader("Baseline Integrated Ranking")

bir1, bir2, bir3, bir4 = st.columns(4)
bir1.metric("Preferred Alternative", baseline_integrated_winner)
bir2.metric("Environmental Weight", f"{environmental_weight_pct}%")
bir3.metric("Economic Weight", f"{economic_weight_pct}%")
bir4.metric("LCIA Categories", f"{len(selected_integrated_impacts)}")

baseline_integrated_display = baseline_integrated[[
    "Rank",
    "Technology",
    "Composite Environmental Score",
    "Recalculated NPV (€)",
    "Economic Score",
    "Integrated Score",
]].rename(columns={"Recalculated NPV (€)": "Baseline NPV (€)"})

st.dataframe(
    baseline_integrated_display,
    use_container_width=True,
    hide_index=True,
)

# ------------------------------------------------------------
# MONTE CARLO INTEGRATED SCORE ENGINE
# ------------------------------------------------------------

ranking_integrated_wide = ranking_wide[common_technologies].copy()

# Economic normalization is scenario-specific.
row_min = ranking_integrated_wide.min(axis=1)
row_max = ranking_integrated_wide.max(axis=1)
row_range = (row_max - row_min).replace(0, np.nan)
economic_scores_wide = (
    ranking_integrated_wide.sub(row_min, axis=0)
    .div(row_range, axis=0)
    .fillna(0.5)
)

# Environmental composite score for every Monte Carlo scenario.
# At 0% LCIA uncertainty, repeat the deterministic composite score.
if lcia_uncertainty <= 0:
    env_composite_map = environmental_composite.set_index("Technology")["Composite Environmental Score"]
    environmental_scores_wide = pd.DataFrame(
        {
            tech: np.repeat(float(env_composite_map.loc[tech]), n_mc)
            for tech in common_technologies
        },
        index=ranking_integrated_wide.index,
    )
else:
    # Build category-specific normalized scores in each scenario and aggregate
    # them using the selected category weights.
    environmental_scores_wide = pd.DataFrame(
        0.0,
        index=ranking_integrated_wide.index,
        columns=common_technologies,
    )

    for impact_index, impact in enumerate(selected_integrated_impacts):
        impact_values = (
            lca_decision[lca_decision["Impact category"] == impact]
            .set_index("Technology")["Result"]
            .reindex(common_technologies)
        )

        impact_sim = pd.DataFrame(index=ranking_integrated_wide.index)
        for tech_index, tech in enumerate(common_technologies):
            local_rng = np.random.default_rng(
                int(mc_seed) + 900001 + 1009 * (impact_index + 1) + 7919 * (tech_index + 1)
            )
            multiplier = triangular_multipliers(local_rng, lcia_uncertainty, n_mc)
            impact_sim[tech] = float(impact_values.loc[tech]) * multiplier

        impact_min = impact_sim.min(axis=1)
        impact_max = impact_sim.max(axis=1)
        impact_range = (impact_max - impact_min).replace(0, np.nan)
        impact_scores = (
            impact_sim.rsub(impact_max, axis=0)
            .div(impact_range, axis=0)
            .fillna(0.5)
        )

        environmental_scores_wide = environmental_scores_wide.add(
            impact_scores * float(category_weight_map[impact]),
            fill_value=0.0,
        )

integrated_scores_wide = pd.DataFrame(index=ranking_integrated_wide.index)
for tech in common_technologies:
    integrated_scores_wide[tech] = (
        w_env * environmental_scores_wide[tech]
        + w_eco * economic_scores_wide[tech]
    )

integrated_winner_each_simulation = integrated_scores_wide.idxmax(axis=1)

integrated_ranking_probability = (
    integrated_winner_each_simulation.value_counts(normalize=True)
    .mul(100)
    .reindex(common_technologies, fill_value=0.0)
    .rename_axis("Technology")
    .reset_index(name="Probability Preferred (%)")
    .sort_values("Probability Preferred (%)", ascending=False)
)

prob_baseline_integrated_winner = float(
    integrated_ranking_probability.loc[
        integrated_ranking_probability["Technology"] == baseline_integrated_winner,
        "Probability Preferred (%)",
    ].iloc[0]
)

reversal_probability = 100.0 - prob_baseline_integrated_winner

challenger_df = integrated_ranking_probability[
    integrated_ranking_probability["Technology"] != baseline_integrated_winner
].copy()

if challenger_df.empty:
    main_challenger = "None"
    main_challenger_probability = 0.0
else:
    main_challenger = challenger_df.iloc[0]["Technology"]
    main_challenger_probability = float(challenger_df.iloc[0]["Probability Preferred (%)"])

# ------------------------------------------------------------
# INTEGRATED DECISION ROBUSTNESS RESULTS
# ------------------------------------------------------------

st.subheader("Integrated Decision Robustness")

idr1, idr2, idr3, idr4 = st.columns(4)
idr1.metric("Baseline Decision", baseline_integrated_winner)
idr2.metric("Decision Robustness", f"{prob_baseline_integrated_winner:.1f}%")
idr3.metric("Reversal Probability", f"{reversal_probability:.1f}%")
idr4.metric("Main Challenger", main_challenger)

integrated_ranking_fig = px.bar(
    integrated_ranking_probability,
    x="Technology",
    y="Probability Preferred (%)",
    text="Probability Preferred (%)",
    labels={"Probability Preferred (%)": "Probability of Integrated Preference (%)"},
)
integrated_ranking_fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
integrated_ranking_fig.update_layout(height=450, yaxis_range=[0, 100])
st.plotly_chart(integrated_ranking_fig, use_container_width=True)
st.dataframe(integrated_ranking_probability, use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# DECISION INTERPRETATION
# ------------------------------------------------------------

st.subheader("Integrated Decision Interpretation")

if prob_baseline_integrated_winner >= 80:
    st.success(
        f"{baseline_integrated_winner} is a highly robust integrated decision under the current "
        f"assumptions, remaining preferred in approximately {prob_baseline_integrated_winner:.1f}% "
        f"of Monte Carlo scenarios."
    )
elif prob_baseline_integrated_winner >= 60:
    st.info(
        f"{baseline_integrated_winner} remains the most robust integrated decision, but the ranking "
        f"is not fully secure. It remains preferred in approximately "
        f"{prob_baseline_integrated_winner:.1f}% of scenarios, with a "
        f"{reversal_probability:.1f}% probability of decision reversal."
    )
else:
    st.warning(
        f"The integrated decision is sensitive to uncertainty and/or weighting preferences. "
        f"{baseline_integrated_winner} is preferred in only "
        f"{prob_baseline_integrated_winner:.1f}% of scenarios. The main challenger is "
        f"{main_challenger} ({main_challenger_probability:.1f}% preferred)."
    )

st.caption(
    "Interpretation boundary: this demo uses normalized midpoint LCIA results and user-defined "
    "decision weights. Equal weighting is a transparent demo assumption, not a universal value judgement. "
    "For real projects, impact-category weights and uncertainty distributions should be justified using "
    "stakeholder preferences, policy priorities, literature, expert elicitation, or another documented MCDA method."
)

# ------------------------------------------------------------
# WEIGHT-SENSITIVITY CURVES FOR ALL TECHNOLOGIES
# ------------------------------------------------------------

st.subheader("Deterministic Integrated Score Across Environmental–Economic Weighting")
st.caption(
    "This diagnostic uses deterministic environmental and economic scores. Each technology line is already the "
    "combined Environmental + Economic score. The probabilistic chart below is the main decision-robustness view."
)

base_score_indexed = baseline_integrated.set_index("Technology")
weight_rows = []
for env_pct in range(0, 101, 2):
    eco_pct = 100 - env_pct
    score = (
        (env_pct / 100.0) * base_score_indexed["Composite Environmental Score"]
        + (eco_pct / 100.0) * base_score_indexed["Economic Score"]
    )
    winner = score.idxmax()
    for technology, integrated_score_value in score.items():
        env_score = float(base_score_indexed.loc[technology, "Composite Environmental Score"])
        eco_score = float(base_score_indexed.loc[technology, "Economic Score"])
        weight_rows.append({
            "Environmental Weight (%)": env_pct,
            "Economic Weight (%)": eco_pct,
            "Technology": technology,
            "Environmental Score": env_score,
            "Economic Score": eco_score,
            "Environmental Contribution": (env_pct / 100.0) * env_score,
            "Economic Contribution": (eco_pct / 100.0) * eco_score,
            "Integrated Score": float(integrated_score_value),
            "Preferred": technology == winner,
        })

weight_score_df = pd.DataFrame(weight_rows)

weight_fig = px.line(
    weight_score_df,
    x="Environmental Weight (%)",
    y="Integrated Score",
    color="Technology",
    custom_data=[
        "Economic Weight (%)", "Environmental Score", "Economic Score",
        "Environmental Contribution", "Economic Contribution"
    ],
    labels={
        "Environmental Weight (%)": "Environmental weight (%)",
        "Integrated Score": "Integrated decision score",
        "Technology": "Technology",
    },
)
weight_fig.update_traces(
    hovertemplate=(
        "<b>%{fullData.name}</b><br>"
        "Environmental weight: %{x:.0f}%<br>"
        "Economic weight: %{customdata[0]:.0f}%<br>"
        "Environmental score: %{customdata[1]:.4f}<br>"
        "Economic score: %{customdata[2]:.4f}<br>"
        "Environmental contribution: %{customdata[3]:.4f}<br>"
        "Economic contribution: %{customdata[4]:.4f}<br>"
        "<b>Integrated score: %{y:.4f}</b><extra></extra>"
    )
)
weight_fig.add_vline(
    x=environmental_weight_pct,
    line_dash="dash",
    annotation_text="Current weight",
    annotation_position="top"
)
weight_fig.update_layout(height=520, legend_title_text="Technology", yaxis_range=[0, 1.05])
st.plotly_chart(weight_fig, use_container_width=True)

# Score composition at the currently selected top-level weighting.
current_weight_rows = []
for technology in base_score_indexed.index:
    env_score = float(base_score_indexed.loc[technology, "Composite Environmental Score"])
    eco_score = float(base_score_indexed.loc[technology, "Economic Score"])
    env_contribution = w_env * env_score
    eco_contribution = w_eco * eco_score
    current_weight_rows.append({
        "Technology": technology,
        "Environmental Score": env_score,
        "Economic Score": eco_score,
        "Environmental Contribution": env_contribution,
        "Economic Contribution": eco_contribution,
        "Integrated Score": env_contribution + eco_contribution,
    })
current_weight_df = pd.DataFrame(current_weight_rows).sort_values(
    "Integrated Score", ascending=False
).reset_index(drop=True)
current_weight_df.insert(0, "Rank", range(1, len(current_weight_df) + 1))

st.markdown("#### Score Composition at Current Weight")
st.caption(
    f"At the current {environmental_weight_pct:.0f}% environmental / {economic_weight_pct:.0f}% economic weighting, "
    "each bar shows how the two weighted contributions add up to the integrated score."
)
composition_long = current_weight_df.melt(
    id_vars=["Technology"],
    value_vars=["Environmental Contribution", "Economic Contribution"],
    var_name="Contribution",
    value_name="Weighted Contribution",
)
composition_fig = px.bar(
    composition_long,
    x="Technology",
    y="Weighted Contribution",
    color="Contribution",
    barmode="stack",
    labels={"Weighted Contribution": "Contribution to integrated score"},
)
composition_fig.update_layout(height=420, legend_title_text="Score component", yaxis_range=[0, 1.05])
st.plotly_chart(composition_fig, use_container_width=True)
st.dataframe(current_weight_df, use_container_width=True, hide_index=True)

# Winner-only frame retained for deterministic switch detection.
weight_sensitivity_df = (
    weight_score_df[weight_score_df["Preferred"]]
    [["Environmental Weight (%)", "Economic Weight (%)", "Technology", "Integrated Score"]]
    .rename(columns={"Technology": "Preferred Technology", "Integrated Score": "Winning Score"})
    .sort_values("Environmental Weight (%)")
    .reset_index(drop=True)
)
weight_sensitivity_df["Switch"] = (
    weight_sensitivity_df["Preferred Technology"]
    != weight_sensitivity_df["Preferred Technology"].shift(1)
)
weight_switches = weight_sensitivity_df[
    weight_sensitivity_df["Switch"] & (weight_sensitivity_df.index > 0)
].copy()
if weight_switches.empty:
    st.info(
        "Deterministic weighting alone does not create a switch from 0% to 100% environmental weight. "
        "This means the same technology has the highest deterministic integrated score across this weight range; "
        "it does not mean that it wins every Monte Carlo scenario."
    )
else:
    switch_text = "; ".join(
        f"around {int(row['Environmental Weight (%)'])}% environmental weight → {row['Preferred Technology']}"
        for _, row in weight_switches.iterrows()
    )
    st.info(f"Approximate deterministic decision-switch points: {switch_text}.")

# ------------------------------------------------------------
# PROBABILISTIC PREFERENCE ACROSS ENVIRONMENTAL–ECONOMIC WEIGHTS
# ------------------------------------------------------------
st.subheader("Probabilistic Preference Across Environmental–Economic Weighting")
st.caption(
    "This is the main robustness chart. For every environmental weight, the dashboard recombines the Monte Carlo "
    "economic score and environmental score in every simulation, then reports how often each technology is preferred. "
    "At 0% environmental weight, this reduces to the Monte Carlo economic ranking by NPV."
)

prob_weight_rows = []
for env_pct in range(0, 101, 2):
    env_w = env_pct / 100.0
    eco_w = 1.0 - env_w
    score_wide = environmental_scores_wide * env_w + economic_scores_wide * eco_w
    winner_each = score_wide.idxmax(axis=1)
    probabilities = winner_each.value_counts(normalize=True).mul(100).reindex(common_technologies, fill_value=0.0)
    for technology in common_technologies:
        prob_weight_rows.append({
            "Environmental Weight (%)": env_pct,
            "Economic Weight (%)": 100 - env_pct,
            "Technology": technology,
            "Probability Preferred (%)": float(probabilities.loc[technology]),
        })

prob_weight_df = pd.DataFrame(prob_weight_rows)
prob_weight_fig = px.line(
    prob_weight_df,
    x="Environmental Weight (%)",
    y="Probability Preferred (%)",
    color="Technology",
    custom_data=["Economic Weight (%)"],
    labels={
        "Environmental Weight (%)": "Environmental weight (%)",
        "Probability Preferred (%)": "Probability preferred (%)",
        "Technology": "Technology",
    },
)
prob_weight_fig.update_traces(
    hovertemplate=(
        "<b>%{fullData.name}</b><br>"
        "Environmental weight: %{x:.0f}%<br>"
        "Economic weight: %{customdata[0]:.0f}%<br>"
        "<b>Probability preferred: %{y:.1f}%</b><extra></extra>"
    )
)
prob_weight_fig.add_vline(
    x=environmental_weight_pct,
    line_dash="dash",
    annotation_text="Current weight",
    annotation_position="top"
)
prob_weight_fig.update_layout(height=520, legend_title_text="Technology", yaxis_range=[0, 100])
st.plotly_chart(prob_weight_fig, use_container_width=True)

# Sanity check: at 0% environmental weight, probabilistic preference must equal NPV-only MC ranking.
prob_zero = (
    prob_weight_df[prob_weight_df["Environmental Weight (%)"] == 0]
    .set_index("Technology")["Probability Preferred (%)"]
    .reindex(common_technologies)
)
mc_npv_prob = (
    ranking_wide.idxmax(axis=1).value_counts(normalize=True).mul(100)
    .reindex(common_technologies, fill_value=0.0)
)
max_zero_diff = float((prob_zero - mc_npv_prob).abs().max())
if max_zero_diff < 1e-9:
    st.success("Sanity check passed: at 0% environmental weight, the preference probabilities match the NPV-only Monte Carlo ranking.")
else:
    st.warning(f"Sanity check difference at 0% environmental weight: {max_zero_diff:.4f} percentage points.")

current_prob_df = (
    prob_weight_df[prob_weight_df["Environmental Weight (%)"] == int(round(environmental_weight_pct / 2.0) * 2)]
    [["Technology", "Probability Preferred (%)"]]
    .sort_values("Probability Preferred (%)", ascending=False)
    .reset_index(drop=True)
)
st.dataframe(current_prob_df, use_container_width=True, hide_index=True)

st.caption(
    "For this public demo, Monte Carlo sample size controls numerical convergence, while uncertainty ranges, "
    "LCIA scope, LCIA uncertainty and decision weights control the substantive spread and ranking. Increasing "
    "the number of simulations alone should not materially change a converged result."
)
