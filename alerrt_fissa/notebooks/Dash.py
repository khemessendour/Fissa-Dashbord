# ===============================
# IMPORTS
# ===============================
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()

# ===============================
# PAGE CONFIG & STYLE
# ===============================
st.set_page_config(
    page_title="🌡️ Fever Syndromic Dashboard",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {background-color: #f0f2f6;}
    .stButton>button {background-color: #4CAF50; color: white; font-weight: bold;}
    h1 {color: #1f77b4;}
    .metric-label {font-size:14px; color:#555;}
    </style>
""", unsafe_allow_html=True)

# ===============================
# HEADER TITLE
# ===============================
st.markdown("""
    <div style="background-color:#1f77b4; padding:20px; border-radius:10px; text-align:center">
        <h1 style="color:white; margin:0">🌡️ Fever Syndromic Surveillance Dashboard</h1>
        <p style="color:white; font-size:16px">Interactive Dashboard for Epidemic Monitoring</p>
    </div>
""", unsafe_allow_html=True)

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data():
    path = os.getenv("CLEAN_DATA_FILE_PATH")
    if not path:
        raise ValueError("CLEAN_DATA_FILE_PATH not found in .env")
    df = pd.read_csv(path)
    df["date_inclusion"] = pd.to_datetime(df["date_inclusion"], errors="coerce")
    disease_cols = ["Arbovirus", "ILI", "SARI", "Diarrhoea", "Malaria_case"]
    df[disease_cols] = df[disease_cols].apply(pd.to_numeric, errors="coerce")
    return df

# ===============================
# SIDEBAR
# ===============================
def sidebar(df):
    st.sidebar.header("🛠️ Filters")
    st.sidebar.markdown("Refine your data using the filters below:")

    # Country
    countries = ["All"] + sorted(df["country"].dropna().unique())
    country = st.sidebar.selectbox("🌍 Country", countries)
    st.sidebar.caption("Select a country to filter the data")

    # Disease
    disease = st.sidebar.selectbox(
        "🦠 Disease",
        ["Arbovirus", "ILI", "SARI", "Diarrhoea", "Malaria_case"]
    )
    st.sidebar.caption("Choose the disease of interest")

    # Aggregation Frequency
    freq = st.sidebar.radio("📊 Aggregation Frequency", ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"])
    st.sidebar.caption("Select how data should be aggregated")

    # Date range
    min_d, max_d = df["date_inclusion"].min(), df["date_inclusion"].max()
    dates = st.sidebar.date_input("📅 Date range", [min_d, max_d], min_value=min_d, max_value=max_d)
    st.sidebar.caption("Choose the time period for analysis")

    if len(dates) == 1:
        dates = [dates[0], dates[0]]

    return country, disease, freq, dates

# ===============================
# FILTER DATA
# ===============================
def filter_data(df, country, dates):
    df = df[(df["date_inclusion"] >= pd.to_datetime(dates[0])) &
            (df["date_inclusion"] <= pd.to_datetime(dates[1]))].copy()
    if country != "All":
        df = df[df["country"] == country]
    return df

# ===============================
# GROUP DATA
# ===============================
def group_data(df, disease, freq):
    if freq == "Daily":
        g = df.groupby(df["date_inclusion"].dt.date)[disease].sum()
    elif freq == "Weekly":
        g = df.groupby(df["date_inclusion"].dt.to_period("W"))[disease].sum()
    elif freq == "Monthly":
        g = df.groupby(df["date_inclusion"].dt.to_period("M"))[disease].sum()
    elif freq == "Quarterly":
        g = df.groupby(df["date_inclusion"].dt.to_period("Q"))[disease].sum()
    else:
        g = df.groupby(df["date_inclusion"].dt.to_period("Y"))[disease].sum()
    g.index = g.index.astype(str)
    return g

# ===============================
# KPIs
# ===============================
def compute_kpis(df, grouped, disease):
    total = int(grouped.sum()) if not grouped.empty else 0
    peak = str(grouped.idxmax()) if not grouped.empty else "N/A"
    cases = df[df[disease] == 1].copy()
    male = cases["gender"].value_counts().get("Male", 0)
    female = cases["gender"].value_counts().get("Female", 0)
    tot = male + female
    male_pct = int(male / tot * 100) if tot else 0
    female_pct = int(female / tot * 100) if tot else 0
    return total, peak, male_pct, female_pct, cases

# ===============================
# MAIN APP
# ===============================
def main():
    df = load_data()
    country, disease, freq, dates = sidebar(df)
    df_f = filter_data(df, country, dates)
    grouped = group_data(df_f, disease, freq)
    total, peak, male_pct, female_pct, cases = compute_kpis(df_f, grouped, disease)

    # ===============================
    # KPI CARDS
    # ===============================
    c1, c2, c3 = st.columns(3)
    c1.metric("Total cases", total, delta=f"{total - grouped.mean():.0f} from mean")
    c2.metric("Peak period", peak)
    c3.metric("Male : Female", f"{male_pct}% : {female_pct}%")

    # ===============================
    # TABS
    # ===============================
    tabs = st.tabs([
        "📈 Trends",
        "🚨 Alerts",
        "👥 Gender",
        "📊 Cumulative",
        "📑 Descriptive statistics",
        "📉 Comparison",
        "🎂 Age Groups",
        "🤒 Symptoms",
        "🗓️ Seasonality",
        "✅ Data Quality"
    ])

    # ===============================
    # Trends
    # ===============================
    with tabs[0]:
        st.subheader("📈 Trends")
        fig = px.bar(
            x=grouped.index, y=grouped.values,
            labels={"x": "Period", "y": "Cases"},
            color=grouped.values,
            color_continuous_scale="Blues",
            title=f"{disease} cases over time"
        )
        # Ligne rouge qui suit exactement les barres
        fig.add_scatter(
            x=grouped.index,
            y=grouped.values,
            mode="lines+markers",
            line=dict(color="red", width=3),
            name="Trend"
        )
        st.plotly_chart(fig, use_container_width=True)

    # ===============================
    # Alerts
    # ===============================
    with tabs[1]:
        st.subheader("🚨 Epidemic Alert System")
        baseline = grouped.mean()
        threshold = baseline + 2 * grouped.std()
        st.markdown(f"**Baseline (mean):** {baseline:.2f}")
        st.markdown(f"**Alert threshold (mean + 2σ):** {threshold:.2f}")
        alerts = grouped[grouped > threshold]
        if alerts.empty:
            st.success("🟢 No epidemic signal detected.")
        else:
            st.error("🔴 Epidemic signal detected")
            st.dataframe(alerts.reset_index(name="Cases"))
            st.download_button(
                "Download alert periods",
                alerts.reset_index().to_csv(index=False).encode("utf-8"),
                "alerts.csv",
                "text/csv"
            )

    # ===============================
    # Gender
    # ===============================
    with tabs[2]:
        if not cases.empty:
            fig_gender = px.pie(cases, names="gender", title="Gender Distribution",
                                color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_gender, use_container_width=True)

    # ===============================
    # Cumulative
    # ===============================
    with tabs[3]:
        fig_cum = px.line(grouped.cumsum(), title="Cumulative Cases Over Time")
        fig_cum.update_traces(mode="lines+markers")
        st.plotly_chart(fig_cum, use_container_width=True)

    # ===============================
    # Descriptive statistics
    # ===============================
    with tabs[4]:
        if not grouped.empty:
            stats_df = pd.DataFrame({
                "Statistic": ["Mean", "Median", "Std Dev", "Min", "Max", "Observations"],
                "Value": [grouped.mean(), grouped.median(), grouped.std(), grouped.min(), grouped.max(), grouped.count()]
            })
            st.dataframe(stats_df)
        else:
            st.warning("No data available.")

    # ===============================
    # Comparison
    # ===============================
    with tabs[5]:
        compare = df_f.groupby(df_f["date_inclusion"].dt.to_period("M"))[
            ["Arbovirus", "ILI", "SARI", "Diarrhoea", "Malaria_case"]
        ].sum()
        compare.index = compare.index.astype(str)
        fig_compare = px.line(compare, title="Comparison of Diseases Over Time")
        st.plotly_chart(fig_compare, use_container_width=True)

    # ===============================
    # Age groups
    # ===============================
    with tabs[6]:
        if "age" in cases.columns:
            cases["age_group"] = pd.cut(cases["age"], [0, 5, 15, 50, 120], labels=["<5", "5–14", "15–49", "50+"])
            fig_age = px.bar(cases["age_group"].value_counts(), title="Cases by Age Group",
                             color=cases["age_group"].value_counts().index)
            st.plotly_chart(fig_age, use_container_width=True)

    # ===============================
    # Symptoms
    # ===============================
    with tabs[7]:
        sym_cols = [c for c in df.columns if c.startswith("sym_")]
        if sym_cols:
            cases[sym_cols] = cases[sym_cols].apply(pd.to_numeric, errors="coerce")
            fig_sym = px.bar(cases[sym_cols].sum(), title="Symptoms Counts",
                             color=cases[sym_cols].sum().index)
            st.plotly_chart(fig_sym, use_container_width=True)

    # ===============================
    # Seasonality
    # ===============================
    with tabs[8]:
        df_f["month"] = df_f["date_inclusion"].dt.month
        season = df_f.groupby("month")[disease].sum()
        fig_season = px.bar(season, title="Seasonal Distribution of Cases")
        st.plotly_chart(fig_season, use_container_width=True)

    # ===============================
    # Data Quality
    # ===============================
    with tabs[9]:
        missing = df_f.isna().mean() * 100
        st.dataframe(missing.reset_index(name="% missing"))

    # ===============================
    # Download filtered data
    # ===============================
    download_df = df.copy()
    if country != "All":
        download_df = download_df[download_df["country"] == country]
    download_df = download_df[
        (download_df["date_inclusion"] >= pd.to_datetime(dates[0])) &
        (download_df["date_inclusion"] <= pd.to_datetime(dates[1]))
    ]
    download_df = download_df[download_df[disease] == 1]

    st.sidebar.download_button(
        "Download filtered data",
        download_df.to_csv(index=False).encode("utf-8"),
        f"filtered_data_{disease}_{country}.csv",
        "text/csv"
    )

if __name__ == "__main__":
    main()
