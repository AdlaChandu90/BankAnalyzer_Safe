import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bank Statement Analyzer", layout="wide")

st.title("🏦 Bank Statement Analyzer")

# Upload file
uploaded_file = st.file_uploader("Upload your bank statement (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Read file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("📋 Raw Data Preview")
        st.write(df.head())

        # Detect date column
        date_cols = [col for col in df.columns if "date" in col.lower()]

        if date_cols:
            # Fix date parsing
            df['Date'] = pd.to_datetime(
                df[date_cols[0]],
                errors='coerce',   # invalid values → NaT
                dayfirst=True      # set False if your format is MM/DD/YYYY
            )
        else:
            df['Date'] = pd.NaT

        # Show basic info
        st.subheader("📊 Analysis")
        st.write("✅ Total Rows:", len(df))
        if 'Date' in df:
            st.write("📅 Date Range:", df['Date'].min(), "→", df['Date'].max())

        # Try to detect debit/credit columns
        debit_cols = [col for col in df.columns if "debit" in col.lower()]
        credit_cols = [col for col in df.columns if "credit" in col.lower()]

        if debit_cols:
            total_debit = df[debit_cols[0]].sum(numeric_only=True)
            st.write("💸 Total Debit:", total_debit)

        if credit_cols:
            total_credit = df[credit_cols[0]].sum(numeric_only=True)
            st.write("💰 Total Credit:", total_credit)

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
