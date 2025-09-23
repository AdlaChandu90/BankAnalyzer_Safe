import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(page_title="Bank Statement Analyzer", layout="wide")

st.title("🏦 Bank Statement Analyzer")

uploaded_file = st.file_uploader("📂 Upload your bank statement (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    # Read file
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    # 🔹 Clean column names
    df.columns = df.columns.str.strip().str.lower()

    st.subheader("📋 Raw Data Preview")
    st.dataframe(df.head(50))  # Show more rows

    # 🔹 Debit & Credit
    if "debit" in df.columns and "credit" in df.columns:
        df["debit"] = pd.to_numeric(df["debit"], errors="coerce").fillna(0)
        df["credit"] = pd.to_numeric(df["credit"], errors="coerce").fillna(0)

        total_credit = df["credit"].sum()
        total_debit = df["debit"].sum()
        net_balance = total_credit - total_debit
    else:
        st.warning("⚠️ No 'Debit' and 'Credit' columns found. Check your file.")
        total_credit, total_debit, net_balance = 0, 0, 0

    # 🔹 Dates
    if "value date" in df.columns:
        df["value date"] = pd.to_datetime(df["value date"], errors="coerce")
        date_range = f"{df['value date'].min().date()} → {df['value date'].max().date()}"
    else:
        date_range = "No 'Value Date' column found"

    # 🔹 Analysis Section
    st.subheader("📊 Analysis")
    st.write("✅ **Total Rows:**", len(df))
    st.write("📅 **Date Range:**", date_range)
    st.write("💰 **Total Credit:**", total_credit)
    st.write("💸 **Total Debit:**", total_debit)
    st.write("📌 **Net Balance (Credit - Debit):**", net_balance)

    # 🔹 Charts
    if "value date" in df.columns and "debit" in df.columns and "credit" in df.columns:
        st.subheader("📈 Visual Insights")

        # Group by Date
        daily_summary = df.groupby("value date")[["debit", "credit"]].sum()

        # Bar chart
        st.write("**Daily Debit vs Credit**")
        fig, ax = plt.subplots(figsize=(10, 4))
        daily_summary.plot(kind="bar", ax=ax)
        ax.set_ylabel("Amount")
        ax.set_xlabel("Date")
        ax.set_title("Daily Debit vs Credit")
        st.pyplot(fig)

        # Monthly trend
        st.write("**Monthly Credit vs Debit Trend**")
        monthly_summary = df.groupby(df["value date"].dt.to_period("M"))[["debit", "credit"]].sum()
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        monthly_summary.plot(kind="line", marker="o", ax=ax2)
        ax2.set_ylabel("Amount")
        ax2.set_xlabel("Month")
        ax2.set_title("Monthly Trend")
        st.pyplot(fig2)

    # 🔹 Download Report
    st.subheader("📥 Download Report")
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="BankStatement")
        st.download_button(
            label="⬇️ Download Excel Report",
            data=output.getvalue(),
            file_name="BankStatementReport.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"⚠️ Error creating report: {e}")
