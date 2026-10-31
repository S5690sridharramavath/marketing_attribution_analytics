"""Interactive Streamlit dashboard for Marketing Attribution & ROI Analytics.

The dashboard reads analytical CSV reports only. It does not modify source data,
run the generator, or use ground-truth labels to calculate business metrics.

Run from the repository root:
    python -m pip install -r requirements.txt
    python -m streamlit run dashboard/app.py

To point at a different report directory:
    # PowerShell
    $env:REPORTS_DIR = "output/full/reports"
    python -m streamlit run dashboard/app.py
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd
import streamlit as st


# -----------------------------------------------------------------------------
# Page setup and configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Marketing Attribution & ROI Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", str(DEFAULT_REPORTS_DIR))).expanduser()

REQUIRED_COLUMNS: Dict[str, set[str]] = {
    "model_comparison.csv": {
        "model_id", "variant", "total_revenue_usd", "unattributed_share",
        "portfolio_roi", "channel_roi_rank_stability_train_vs_test",
    },
    "channel_roi.csv": {
        "channel_name", "model_id", "variant", "period",
        "attributed_revenue_usd", "cost_usd", "roi",
    },
    "attribution_report.csv": {
        "campaign_id", "channel_name", "model_id", "variant", "period",
        "attributed_revenue_usd", "cost_usd", "roi", "cost_status",
    },
    "exceptions.csv": {"issue_type", "entity_id", "decision_applied"},
}


# -----------------------------------------------------------------------------
# Data loading and validation
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_csv(path_string: str, modified_time: float) -> pd.DataFrame:
    """Load a CSV and cache it until the file's modification time changes."""
    del modified_time  # Included in the cache key to invalidate stale data.
    return pd.read_csv(path_string)


def load_reports(directory: Path) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Load the four dashboard reports and return any actionable errors."""
    frames: dict[str, pd.DataFrame] = {}
    errors: list[str] = []

    for filename, required in REQUIRED_COLUMNS.items():
        path = directory / filename
        if not path.is_file():
            errors.append(f"Missing file: `{path}`")
            continue
        try:
            frame = load_csv(str(path), path.stat().st_mtime)
        except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
            errors.append(f"Could not read `{filename}`: {exc}")
            continue

        missing = sorted(required.difference(frame.columns))
        if missing:
            errors.append(
                f"`{filename}` is missing required columns: {', '.join(missing)}"
            )
            continue
        frames[filename] = frame

    return frames, errors


def money(value: float) -> str:
    if pd.isna(value):
        return "—"
    return f"${value:,.0f}"


def percent(value: float) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:.1%}"


def roi_label(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}x"


def safe_numeric(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


# -----------------------------------------------------------------------------
# Header and sidebar
# -----------------------------------------------------------------------------
st.title("📊 Marketing Attribution & ROI Analytics")
st.caption(
    "Explore attribution models, channel performance, campaign ROI and data-quality exceptions. "
    "All figures are read from the project's generated CSV reports."
)

with st.sidebar:
    st.header("Dashboard controls")
    st.caption("Choose which generated report set to inspect.")
    reports_input = st.text_input("Reports directory", value=str(REPORTS_DIR))
    active_reports_dir = Path(reports_input).expanduser()
    st.divider()
    st.caption("Tip: use `output/full/reports` to inspect the full-scale run.")
    if st.button("Refresh report data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

reports, load_errors = load_reports(active_reports_dir)
if load_errors:
    st.error("The dashboard could not load all required reports.")
    for error in load_errors:
        st.write(f"- {error}")
    st.info(
        "Run the project pipeline first, or set the Reports directory to a folder "
        "containing model_comparison.csv, channel_roi.csv, attribution_report.csv "
        "and exceptions.csv."
    )
    st.stop()

model_comparison = safe_numeric(
    reports["model_comparison.csv"],
    ["total_revenue_usd", "unattributed_revenue_usd", "unattributed_share",
     "portfolio_roi", "channel_roi_rank_stability_train_vs_test",
     "campaign_credit_per_engaged_touch_vs_latent_quality_spearman"],
)
channel_roi = safe_numeric(
    reports["channel_roi.csv"],
    ["attributed_revenue_usd", "cost_usd", "roi"],
)
campaign_roi = safe_numeric(
    reports["attribution_report.csv"],
    ["attributed_revenue_usd", "cost_usd", "roi"],
)
exceptions = reports["exceptions.csv"]

# Filters are based on values present in the report rather than hard-coded lists.
variants = sorted(model_comparison["variant"].dropna().astype(str).unique().tolist())
periods = sorted(channel_roi["period"].dropna().astype(str).unique().tolist())
model_names = sorted(model_comparison["model_id"].dropna().astype(str).unique().tolist())

with st.sidebar:
    selected_variant = st.selectbox(
        "Data variant", variants,
        index=variants.index("clean") if "clean" in variants else 0,
        help="Clean applies the documented anomaly decisions; raw retains the original edge cases.",
    )
    selected_period = st.selectbox(
        "Evaluation period", ["all"] + [p for p in periods if p != "all"],
        index=0,
    )
    selected_models = st.multiselect(
        "Attribution models", model_names, default=model_names,
    )

# -----------------------------------------------------------------------------
# Global summary
# -----------------------------------------------------------------------------
filtered_models = model_comparison[
    (model_comparison["variant"] == selected_variant)
    & model_comparison["model_id"].isin(selected_models)
].copy()

if filtered_models.empty:
    st.warning("No model results match the selected filters. Select at least one available model.")
    st.stop()

# Revenue is shared across attribution models; use one value, not a sum across models.
revenue_value = filtered_models["total_revenue_usd"].dropna().iloc[0] if filtered_models["total_revenue_usd"].notna().any() else float("nan")
unattributed_value = filtered_models["unattributed_share"].dropna().iloc[0] if filtered_models["unattributed_share"].notna().any() else float("nan")
best_row = filtered_models.sort_values("portfolio_roi", ascending=False, na_position="last").head(1)
best_model = str(best_row.iloc[0]["model_id"]) if not best_row.empty else "—"
best_roi = best_row.iloc[0]["portfolio_roi"] if not best_row.empty else float("nan")

st.subheader("Performance overview")
metric_cols = st.columns(4)
metric_cols[0].metric("Total revenue", money(revenue_value))
metric_cols[1].metric("Unattributed revenue share", percent(unattributed_value))
metric_cols[2].metric("Best portfolio ROI", roi_label(best_roi), help="Highest portfolio ROI among the selected models.")
metric_cols[3].metric("Models selected", f"{len(filtered_models):,}")
st.caption(f"Report source: `{active_reports_dir.resolve()}`  ·  Variant: **{selected_variant}**")
st.divider()

# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------
tab_models, tab_channels, tab_campaigns, tab_exceptions = st.tabs(
    ["Model comparison", "Channel performance", "Campaign performance", "Data quality"]
)

with tab_models:
    st.subheader("Attribution model comparison")
    display = filtered_models.sort_values("portfolio_roi", ascending=False).copy()
    st.bar_chart(display.set_index("model_id")[["portfolio_roi"]])

    model_columns = [
        "model_id", "total_revenue_usd", "unattributed_share", "portfolio_roi",
        "channel_roi_rank_stability_train_vs_test",
        "campaign_credit_per_engaged_touch_vs_latent_quality_spearman",
    ]
    st.dataframe(
        display[model_columns].rename(columns={
            "model_id": "Attribution model",
            "total_revenue_usd": "Revenue (USD)",
            "unattributed_share": "Unattributed share",
            "portfolio_roi": "Portfolio ROI",
            "channel_roi_rank_stability_train_vs_test": "Rank stability (train vs test)",
            "campaign_credit_per_engaged_touch_vs_latent_quality_spearman": "Credit / latent quality correlation",
        }),
        use_container_width=True,
        hide_index=True,
    )
    st.info(
        "Rank stability compares channel ROI rankings between training and test periods. "
        "The quality-correlation metric is an evaluation diagnostic, not a production input."
    )

with tab_channels:
    st.subheader("Channel-level ROI")
    channel_view = channel_roi[
        (channel_roi["variant"] == selected_variant)
        & (channel_roi["period"] == selected_period)
        & channel_roi["model_id"].isin(selected_models)
    ].copy()

    if channel_view.empty:
        st.info("No channel results match the selected filters.")
    else:
        pivot = channel_view.pivot_table(
            index="channel_name", columns="model_id", values="roi", aggfunc="mean"
        )
        st.bar_chart(pivot)
        st.dataframe(
            channel_view.sort_values("roi", ascending=False, na_position="last"),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download filtered channel results",
            channel_view.to_csv(index=False).encode("utf-8"),
            file_name="channel_roi_filtered.csv",
            mime="text/csv",
        )

with tab_campaigns:
    st.subheader("Campaign-level performance")
    if not selected_models:
        st.info("Select at least one attribution model in the sidebar.")
    else:
        chosen_campaign_model = st.selectbox(
            "Attribution model", selected_models, key="campaign_model"
        )
        campaign_view = campaign_roi[
            (campaign_roi["variant"] == selected_variant)
            & (campaign_roi["period"] == selected_period)
            & (campaign_roi["model_id"] == chosen_campaign_model)
        ].copy()

        if campaign_view.empty:
            st.info("No campaign results match the selected filters.")
        else:
            sort_choice = st.selectbox(
                "Sort campaigns by", ["ROI (highest first)", "Revenue (highest first)", "Cost (highest first)"]
            )
            sort_column = {
                "ROI (highest first)": "roi",
                "Revenue (highest first)": "attributed_revenue_usd",
                "Cost (highest first)": "cost_usd",
            }[sort_choice]
            campaign_view = campaign_view.sort_values(
                sort_column, ascending=False, na_position="last"
            )
            st.caption(
                "Campaigns without cost data have undefined ROI (NULL). They are not treated as zero-cost campaigns."
            )
            st.dataframe(campaign_view, use_container_width=True, hide_index=True)
            st.download_button(
                "Download filtered campaign results",
                campaign_view.to_csv(index=False).encode("utf-8"),
                file_name="campaign_roi_filtered.csv",
                mime="text/csv",
            )

with tab_exceptions:
    st.subheader("Detected data-quality exceptions")
    st.caption("These records show detected issues and the documented handling decision.")
    if exceptions.empty:
        st.success("No exception records were found in this report.")
    else:
        summary = (
            exceptions.groupby(["issue_type", "decision_applied"], dropna=False)
            .size().reset_index(name="records")
            .sort_values("records", ascending=False)
        )
        st.bar_chart(
            exceptions.groupby("issue_type").size().sort_values(ascending=False)
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)
        with st.expander("Inspect individual exception records"):
            st.dataframe(exceptions, use_container_width=True, hide_index=True)
        st.download_button(
            "Download exception records",
            exceptions.to_csv(index=False).encode("utf-8"),
            file_name="exceptions.csv",
            mime="text/csv",
        )

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.divider()
st.caption(
    "Marketing Attribution & ROI Analytics · Synthetic data project · "
    "Dashboard is read-only and does not use ground-truth data to calculate reported ROI."
)
