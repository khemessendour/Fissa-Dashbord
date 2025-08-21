
# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
load_dotenv()

# ---- Load dataset ----
df = pd.read_csv(os.getenv('CLEAN_DATA_FILE_PATH'),  parse_dates=["date_inc"])
df["sexe"] = df["sexe"].map({1: "Male", 2: "Female"})

# ---- Sidebar ----
st.sidebar.header("Filters")
disease = st.sidebar.selectbox("Select Disease", ["arbovirus", "influenza"])
freq = st.sidebar.radio("Aggregation Level", ["Daily", "Weekly", "Monthly"])
min_date, max_date = df["date_inc"].min(), df["date_inc"].max()
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# ---- Filter dataset ----
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
df_filtered = df[(df["date_inc"] >= start_date) & (df["date_inc"] <= end_date)]

# ---- Group data ----
if freq == "Daily":
    grouped = df_filtered.groupby(df_filtered["date_inc"].dt.date)[disease].sum()
    compare_grouped = df_filtered.groupby(df_filtered["date_inc"].dt.date)[["arbovirus", "influenza"]].sum()
elif freq == "Weekly":
    grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("W"))[disease].sum()
    grouped.index = grouped.index.astype(str)
    compare_grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("W"))[["arbovirus", "influenza"]].sum()
    compare_grouped.index = compare_grouped.index.astype(str)
elif freq == "Monthly":
    grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("M"))[disease].sum()
    grouped.index = grouped.index.astype(str)
    compare_grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("M"))[["arbovirus", "influenza"]].sum()
    compare_grouped.index = compare_grouped.index.astype(str)

# ---- Calculate KPIs ----
total_cases = int(grouped.sum()) if not grouped.empty else 0
peak_period = grouped.idxmax() if not grouped.empty else "N/A"
cases_data = df_filtered[df_filtered[disease]==1]
male_count = cases_data["sexe"].value_counts().get("Male", 0)
female_count = cases_data["sexe"].value_counts().get("Female", 0)
total_gender = male_count + female_count
male_pct = round(male_count/total_gender*100,1) if total_gender else 0
female_pct = round(female_count/total_gender*100,1) if total_gender else 0

# ---- Display KPI metrics ----
st.title("Fever Syndromic Surveillance Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric(f"Total {disease.capitalize()} Cases", f"{total_cases:,}")
col2.metric("Peak Period", f"{peak_period}")
col3.metric("Male:Female Ratio", f"{male_pct}% : {female_pct}%")

# ---- Tabs ----
tab1, tab2, tab3, tab4 = st.tabs([f"{disease.capitalize()} Cases", "Gender Distribution", "Cumulative Cases", "Comparison & Peaks"])

# Helper function for x-axis ticks
def set_xaxis_ticks(fig, data_index):
    max_ticks = 10
    tickvals = data_index[::max(1, len(data_index)//max_ticks)]
    ticktext = [str(d) for d in tickvals]
    fig.update_xaxes(tickvals=tickvals, ticktext=ticktext, tickangle=-45)

# ========== TAB 1: Cases ==========
with tab1:
    st.subheader(f"{disease.capitalize()} cases per {freq.lower()[:-2] if freq!='Daily' else 'day'}")
    if grouped.empty:
        st.warning("No data available for the selected filters.")
    else:
        fig = px.bar(
            x=grouped.index, y=grouped.values,
            labels={'x':'Period','y':'Number of Cases'},
            color=grouped.values, color_continuous_scale='Blues'
        )
        set_xaxis_ticks(fig, grouped.index)
        fig.update_layout(showlegend=False)
        fig.update_yaxes(dtick=1)  # <-- integer y-axis
        st.plotly_chart(fig, use_container_width=True)

# ========== TAB 2: Gender Distribution ==========
with tab2:
    st.subheader(f"Gender distribution for {disease.capitalize()} cases")
    if cases_data.empty:
        st.warning("No cases found for this selection.")
    else:
        gender_counts = cases_data["sexe"].value_counts()
        gender_percent = (cases_data["sexe"].value_counts(normalize=True) * 100).round(1)
        fig2 = go.Figure()
        for sex, count, pct, color in zip(gender_counts.index, gender_counts.values, gender_percent.values, ['skyblue','lightcoral']):
            fig2.add_trace(go.Bar(
                x=[sex], y=[count],
                text=[f"{pct}%"],
                textposition='outside',
                marker_color=color,
                name=sex
            ))
        fig2.update_layout(yaxis_title="Number of Cases")
        fig2.update_yaxes(dtick=1)  # <-- integer y-axis
        st.plotly_chart(fig2, use_container_width=True)

# ========== TAB 3: Cumulative Cases ==========
with tab3:
    st.subheader(f"Cumulative {disease.capitalize()} cases over time")
    if grouped.empty:
        st.warning("No data available for the selected filters.")
    else:
        cumulative = grouped.cumsum()
        fig3 = px.line(
            x=cumulative.index, y=cumulative.values,
            labels={'x':'Period','y':'Cumulative Cases'},
            markers=True
        )
        set_xaxis_ticks(fig3, cumulative.index)
        fig3.update_yaxes(dtick=1)  # <-- integer y-axis
        st.plotly_chart(fig3, use_container_width=True)

# ========== TAB 4: Comparison & Peaks ==========
with tab4:
    st.subheader("Arbovirus vs Influenza trends")
    if compare_grouped.empty:
        st.warning("No data available for comparison.")
    else:
        fig4 = px.line(
            compare_grouped, x=compare_grouped.index,
            y=['arbovirus','influenza'],
            labels={'value':'Number of Cases','date_inc':'Period'},
            markers=True
        )
        set_xaxis_ticks(fig4, compare_grouped.index)
        fig4.update_yaxes(dtick=1)  # <-- integer y-axis
        st.plotly_chart(fig4, use_container_width=True)

        # ---- Peak periods table ----
        st.subheader("Top 10 peak periods")
        top_peaks = grouped.sort_values(ascending=False).head(10).reset_index()
        top_peaks.columns = ["Period", "Cases"]
        st.dataframe(top_peaks.style.format({"Cases":"{:,}"}))
