
# # app.py
# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt

# # ---- Load dataset ----
# df = pd.read_csv("/Users/asani/Downloads/HDWRA/alerrt_fissa/cleaned_fissa_gambia_data.csv", parse_dates=["date_inc"])
# # Map sexe codes to labels
# df["sexe"] = df["sexe"].map({1: "Male", 2: "Female"})

# # ---- Sidebar ----
# st.sidebar.header("Filters")

# # Disease selection
# disease = st.sidebar.selectbox("Select Disease", ["arbovirus", "influenza"])

# # Frequency selection
# freq = st.sidebar.radio("Aggregation Level", ["Daily", "Weekly", "Monthly"])

# # Date range filter
# min_date = df["date_inc"].min()
# max_date = df["date_inc"].max()
# date_range = st.sidebar.date_input(
#     "Select Date Range",
#     [min_date, max_date],
#     min_value=min_date,
#     max_value=max_date,
# )

# # ---- Filter dataset ----
# start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
# df_filtered = df[(df["date_inc"] >= start_date) & (df["date_inc"] <= end_date)]

# # ---- Group data ----
# if freq == "Daily":
#     grouped = df_filtered.groupby(df_filtered["date_inc"].dt.date)[disease].sum()
# elif freq == "Weekly":
#     grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("W"))[disease].sum()
# elif freq == "Monthly":
#     grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("M"))[disease].sum()

# # ---- Plot cases ----
# st.subheader(f"{disease.capitalize()} cases per {freq.lower()}")

# if grouped.empty:
#     st.warning("No data available for the selected filters.")
# else:
#     fig, ax = plt.subplots(figsize=(8, 4))
#     grouped.plot(kind="bar", ax=ax, color="steelblue")

#     # Make x-axis readable
#     plt.xticks(rotation=90, ha="right")
#     if freq in ["Daily", "Weekly"]:
#         ax.xaxis.set_major_locator(plt.MaxNLocator(15))  # show max 10 ticks

#     ax.set_ylabel("Number of cases")
#     st.pyplot(fig)

# # ---- Gender distribution ----
# st.subheader(f"Gender distribution for {disease.capitalize()} cases")

# cases = df_filtered[df_filtered[disease] == 1]
# if cases.empty:
#     st.warning("No cases found for this selection.")
# else:
#     gender_counts = cases["sexe"].value_counts(normalize=True) * 100

#     fig2, ax2 = plt.subplots()
#     bars = gender_counts.plot(kind="bar", ax=ax2, color=["skyblue", "lightcoral"])

#     ax2.set_ylabel("Percentage (%)")

#     # Add percentage labels on bars
#     for bar in ax2.patches:
#         ax2.text(
#             bar.get_x() + bar.get_width() / 2,
#             bar.get_height() + 1,
#             f"{bar.get_height():.1f}%",
#             ha="center",
#             va="bottom",
#             fontsize=10,
#         )

#     st.pyplot(fig2)



# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---- Load dataset ----
df = pd.read_csv("/Users/asani/Downloads/HDWRA/alerrt_fissa/cleaned_fissa_gambia_data.csv", parse_dates=["date_inc"])
# Map sexe codes to labels
df["sexe"] = df["sexe"].map({1: "Male", 2: "Female"})

# ---- Sidebar ----
st.sidebar.header("Filters")

# Disease selection
disease = st.sidebar.selectbox("Select Disease", ["arbovirus", "influenza"])

# Frequency selection
freq = st.sidebar.radio("Aggregation Level", ["Daily", "Weekly", "Monthly"])

# Date range filter
min_date = df["date_inc"].min()
max_date = df["date_inc"].max()
date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date,
)

# ---- Filter dataset ----
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
df_filtered = df[(df["date_inc"] >= start_date) & (df["date_inc"] <= end_date)]

# ---- Group data ----
if freq == "Daily":
    grouped = df_filtered.groupby(df_filtered["date_inc"].dt.date)[disease].sum()
elif freq == "Weekly":
    grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("W"))[disease].sum()
elif freq == "Monthly":
    grouped = df_filtered.groupby(df_filtered["date_inc"].dt.to_period("M"))[disease].sum()

# ---- Plot cases ----
st.subheader(f"{disease.capitalize()} cases per {freq.lower()}")

if grouped.empty:
    st.warning("No data available for the selected filters.")
else:
    fig, ax = plt.subplots(figsize=(10, 5))
    grouped.plot(kind="bar", ax=ax, color="steelblue")

    # Make x-axis readable
    plt.xticks(rotation=90, ha="right")
    if freq in ["Daily", "Weekly"]:
        ax.xaxis.set_major_locator(plt.MaxNLocator(10))  # show max 10 ticks

    # Format y-axis as integers
    ax.yaxis.get_major_locator().set_params(integer=True)

    ax.set_ylabel("Number of cases")
    st.pyplot(fig)

# ---- Gender distribution ----
st.subheader(f"Gender distribution for {disease.capitalize()} cases")

cases = df_filtered[df_filtered[disease] == 1]
if cases.empty:
    st.warning("No cases found for this selection.")
else:
    gender_counts = cases["sexe"].value_counts(normalize=True) * 100

    fig2, ax2 = plt.subplots(figsize=(6, 4))
    bars = gender_counts.plot(kind="bar", ax=ax2, color=["skyblue", "lightcoral"])

    ax2.set_ylabel("Percentage (%)")
    ax2.set_ylim(0, gender_counts.max() * 1.2)  # give space for labels

    # Add percentage labels on bars
    for bar in ax2.patches:
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{bar.get_height():.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    st.pyplot(fig2)
