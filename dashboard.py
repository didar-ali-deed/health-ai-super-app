import logging
import sqlite3
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from database import get_patient_history, get_user_predictions

DB_PATH = "health_data.db"


@st.cache_data(ttl=300)
def _fetch_patient_page(user_id: int, page: int, page_size: int):
    """Fetch one page of patient records + total row count. Cached 5 minutes."""
    offset = (page - 1) * page_size
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM patients WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            conn,
            params=(user_id, page_size, offset),
        )
        total = conn.execute(
            "SELECT COUNT(*) FROM patients WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    return df, total


def render_dashboard() -> None:
    """Render the full logged-in dashboard: predictions, metrics, and records."""
    _render_summary()
    _render_records()


def _render_summary() -> None:
    with st.expander("Dashboard", expanded=True):
        try:
            predictions = get_user_predictions(st.session_state.user_id)
            if not predictions.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Predictions", len(predictions))
                    for ptype, count in predictions["prediction_type"].value_counts().items():
                        st.write(f"{ptype}: {count}")
                with col2:
                    fig = px.line(
                        predictions.sort_values("timestamp"),
                        x="timestamp",
                        y="probability",
                        color="prediction_type",
                        title="Prediction Confidence Over Time",
                        labels={"probability": "Confidence (%)", "timestamp": "Date"},
                        height=300,
                    )
                    st.plotly_chart(fig, use_container_width=True)

            history = get_patient_history(st.session_state.user_id)
            if not history.empty:
                latest = history.iloc[0]
                st.write("**Latest Health Metrics**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("BMI", f"{latest['bmi']:.2f}")
                with col2:
                    labels = ["Excellent", "Very Good", "Good", "Fair", "Poor"]
                    idx = int(latest["gen_health"]) - 1
                    st.metric("General Health", labels[idx] if 0 <= idx < 5 else "—")
        except Exception as exc:
            st.warning("Unable to load dashboard data.")
            logging.error("Dashboard error: %s", exc)


def _render_records() -> None:
    st.subheader("Your Health Records", anchor="health-records")

    with st.expander("Search & Filter Records", expanded=False):
        search_query = st.text_input("Search records", placeholder="Search across all fields")
        try:
            history_columns = list(get_patient_history(st.session_state.user_id).columns)
        except Exception:
            history_columns = []
        filter_col = st.selectbox("Filter by", ["All"] + history_columns, key="filter_column")
        sort_by = st.selectbox("Sort by", ["None"] + history_columns, key="sort_by")
        sort_order = st.radio("Sort order", ["Ascending", "Descending"], horizontal=True)

    page_size = st.slider("Records per page", 5, 50, 10, 5, key="page_size")
    page = st.number_input("Page", min_value=1, value=1, step=1, key="page_select")

    try:
        history, total_records = _fetch_patient_page(
            st.session_state.user_id, page, page_size
        )
        if history.empty:
            st.info("No health records available.")
            return

        filtered = history.copy()
        if search_query:
            filtered = filtered[
                filtered.apply(lambda r: search_query.lower() in str(r).lower(), axis=1)
            ]
        if filter_col != "All":
            filtered = filtered[filtered[filter_col].notna()]
        if sort_by != "None":
            filtered = filtered.sort_values(by=sort_by, ascending=(sort_order == "Ascending"))

        total_pages = max(1, (total_records + page_size - 1) // page_size)
        start = (page - 1) * page_size + 1
        end = min(page * page_size, total_records)
        st.caption(f"Showing {start}–{end} of {total_records} records · Page {page} of {total_pages}")

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": "Date & Time",
                "probability": st.column_config.NumberColumn("Probability", format="%.2f"),
                "bmi": st.column_config.NumberColumn("BMI", format="%.2f"),
            },
        )

        st.download_button(
            label="Download Records as CSV",
            data=filtered.to_csv(index=False),
            file_name=f"health_records_{st.session_state.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"Error retrieving records: {exc}")
        logging.error("Health records error: %s", exc)
