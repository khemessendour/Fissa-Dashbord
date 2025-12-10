# Import necessary libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load dataset from .env
@st.cache_data
def load_data():
    data_path = os.getenv('CLEAN_DATA_FILE_PATH')
    if not data_path:
        raise ValueError("CLEAN_DATA_FILE_PATH not found in .env")

    df = pd.read_csv(data_path, parse_dates=["date_inc"])
    df["sexe"] = df["sexe"].map({1: "Male", 2: "Female"})
    return df

# Sidebar filters
def sidebar_filters(df):
    st.sidebar.header("Filters")

    disease = st.sidebar.selectbox("Select Disease", ["arbovirus", "influ_like_ill"])
    freq = st.sidebar.radio("Aggregation Level", ["Daily", "Weekly", "Monthly"])

    min_date, max_date = df["date_inc"].min(), df["date_inc"].max()
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    return disease, freq, date_range


# Filter dataset by date
def filter_data(df, disease, date_range):
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_filtered = df[(df["date_inc"] >= start_date) & (df["date_inc"] <= end_date)]
    return df_filtered


# Group data (Daily / Weekly / Monthly)
def group_data(df_filtered, disease, freq):

    if freq == "Daily":
        grouped = df_filtered.groupby(df_filtered["date_inc"].dt.date)[disease].sum()
        compare_grouped = df_filtered.groupby(df_filtered["date_inc"].dt.date)[["arbovirus", "influ_like_ill"]].sum()

    elif freq == "Weekly":
        grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("W"))[disease].sum()
        grouped.index = grouped.index.astype(str)

        compare_grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("W"))[
            ["arbovirus", "influ_like_ill"]
        ].sum()
        compare_grouped.index = compare_grouped.index.astype(str)

    elif freq == "Monthly":
        grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("M"))[disease].sum()
        grouped.index = grouped.index.astype(str)

        compare_grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("M"))[
            ["arbovirus", "influ_like_ill"]
        ].sum()
        compare_grouped.index = compare_grouped.index.astype(str)

    return grouped, compare_grouped


# Calculate KPI
def calculate_kpis(grouped, df_filtered, disease):

    total_cases = int(grouped.sum()) if not grouped.empty else 0
    peak_period = grouped.idxmax() if not grouped.empty else "N/A"

    try:
        peak_period_fmt = pd.to_datetime(peak_period).strftime('%d-%m-%Y')
    except:
        peak_period_fmt = str(peak_period)

    cases_data = df_filtered[df_filtered[disease] == 1]

    male_count = cases_data["sexe"].value_counts().get("Male", 0)
    female_count = cases_data["sexe"].value_counts().get("Female", 0)
    total_gender = male_count + female_count

    male_pct = int(round(male_count / total_gender * 100, 0)) if total_gender else 0
    female_pct = int(round(female_count / total_gender * 100, 0)) if total_gender else 0

    return total_cases, peak_period_fmt, male_pct, female_pct, cases_data


# Homepage banner + CSS
def homepage_header():
    st.markdown("""
        <style>
            .big-title {
                font-size: 38px;  /* slightly smaller */
                text-align: center;
                color: #003366;
                font-weight: 700;
                margin-bottom: -8px;
            }
            .subtitle {
                text-align: center;
                color: #0077aa;
                font-size: 18px;  /* slightly smaller */
                margin-bottom: 18px;
            }
            .home-box {
                padding: 20px;  /* a bit more compact */
                background-color: #f5f7fa;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="home-box">
            <div class="big-title">Fever Syndromic Surveillance Dashboard</div>
            <div class="subtitle">Temporal Trends of Arbovirus and ILI Cases</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)



# KPI cards
def display_kpis(total_cases, peak_period_fmt, male_pct, female_pct, disease):

    col1, col2, col3 = st.columns(3)

    col1.metric(f"Total {disease.capitalize()} Cases", f"{total_cases:,}")
    col2.metric("Peak Period", f"{peak_period_fmt}")
    col3.metric("Male : Female Ratio", f"{male_pct}% : {female_pct}%")

    st.markdown("<hr>", unsafe_allow_html=True)


# Summary Table
def display_summary_table(total_cases, male_pct, female_pct, cases_data):
    st.subheader("Summary Statistics")

    summary_stats = pd.DataFrame({
        'Metric': ['Total Cases', 'Male (%)', 'Female (%)', 'Average Age'],
        'Value': [
            total_cases,
            f"{male_pct}%",
            f"{female_pct}%",
            int(round(cases_data['age'].mean(), 0)) if 'age' in cases_data and not cases_data.empty else 0,
        ]
    })

    st.table(summary_stats)


# Helper for x-axis readability
def set_xaxis_ticks(fig, data_index):
    max_ticks = 10
    tickvals = data_index[::max(1, len(data_index)//max_ticks)]
    fig.update_xaxes(tickvals=tickvals, tickangle=-45)


# Tabs and charts
def display_tabs(grouped, compare_grouped, cases_data, disease, freq):

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        f"{disease.capitalize()} Cases",
        "Gender Distribution",
        "Cumulative Cases",
        "Comparison & Peaks",
        "Age Groups",
        "Symptoms"
    ])

    # Table 1: Time series
    with tab1:
        st.subheader(f"{disease.capitalize()} Cases Over Time")
        if grouped.empty:
            st.warning("No data available.")
        else:
            fig = px.bar(
                x=grouped.index,
                y=grouped.values,
                labels={"x": "Period", "y": "Cases"},
                color=grouped.values,
                color_continuous_scale="Blues"
            )
            rolling = grouped.rolling(window=7, min_periods=1).mean()
            fig.add_scatter(x=grouped.index, y=rolling, mode="lines", name="7-day Rolling Mean", line=dict(color="red"))
            set_xaxis_ticks(fig, grouped.index)
            st.plotly_chart(fig, use_container_width=True)

    # Table 2: Gender
    with tab2:
        st.subheader("Gender Breakdown")
        if cases_data.empty:
            st.warning("No cases found.")
        else:
            gender_counts = cases_data["sexe"].value_counts()
            fig2 = px.bar(
                x=gender_counts.index,
                y=gender_counts.values,
                labels={"x": "Gender", "y": "Cases"},
                color=gender_counts.values,
                color_continuous_scale="Sunset"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Tab 3: Cumulative
    with tab3:
        st.subheader("Cumulative Cases")
        if grouped.empty:
            st.warning("No data.")
        else:
            cumulative = grouped.cumsum()
            fig3 = px.line(
                x=cumulative.index,
                y=cumulative.values,
                markers=True
            )
            st.plotly_chart(fig3, use_container_width=True)

    # Table 4: Compare Arbovirus vs Influenza
    with tab4:
        st.subheader("Disease Comparison")
        if compare_grouped.empty:
            st.warning("No comparison data.")
        else:
            fig4 = px.line(compare_grouped, markers=True)
            st.plotly_chart(fig4, use_container_width=True)

    # Table 5: Age groups
    with tab5:
        st.subheader("Age Group Distribution")
        if not cases_data.empty and "age" in cases_data:
            bins = [0, 5, 18, 120]
            labels = ["<5", "5–17", "18+"]
            cases_data["age_group"] = pd.cut(cases_data["age"], bins=bins, labels=labels)
            age_counts = cases_data["age_group"].value_counts().sort_index()
            fig_age = px.bar(x=age_counts.index, y=age_counts.values, color=age_counts.values)
            st.plotly_chart(fig_age, use_container_width=True)

    # Table 6: Symptoms
    with tab6:
        st.subheader("Symptom Frequency")
        symptom_cols = [
            'thorax_1','orl_6','thorax_2','thorax_4','syst_nev_1',
            'muscl_1','muscl_2','peau_1','peau_3','thorax_3','orl_5'
        ]
        rename_map = {
            'thorax_1': 'Cough','orl_6':'Dysphagia','thorax_2':'Dyspnea','thorax_4':'Chest Pain',
            'syst_nev_1':'Headache','muscl_1':'Arthralgia','muscl_2':'Myalgia','peau_1':'Skin Rash',
            'peau_3':'Purpura','thorax_3':'Hemoptysis','orl_5':'Eye Pain'
        }

        available = [col for col in symptom_cols if col in cases_data.columns]

        if not available:
            st.warning("No symptom data available.")
        else:
            freq_symptoms = cases_data[available].sum().rename(index=rename_map)
            fig = px.bar(x=freq_symptoms.index, y=freq_symptoms.values, color=freq_symptoms.values)
            st.plotly_chart(fig, use_container_width=True)

# Download Button
def add_download_button(cases_data):
    st.sidebar.download_button(
        label="Download filtered data",
        data=cases_data.to_csv(index=False).encode("utf-8"),
        file_name="filtered_data.csv",
        mime="text/csv"
    )


# Main application
def main():

    df = load_data()

    homepage_header()

    disease, freq, date_range = sidebar_filters(df)

    df_filtered = filter_data(df, disease, date_range)
    grouped, compare_grouped = group_data(df_filtered, disease, freq)

    total_cases, peak_period_fmt, male_pct, female_pct, cases_data = calculate_kpis(
        grouped, df_filtered, disease
    )

    display_kpis(total_cases, peak_period_fmt, male_pct, female_pct, disease)

    display_summary_table(total_cases, male_pct, female_pct, cases_data)

    display_tabs(grouped, compare_grouped, cases_data, disease, freq)

    add_download_button(cases_data)


# Run the app
if __name__ == "__main__":
    main()
