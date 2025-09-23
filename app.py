import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

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
        st.dataframe(df)

        # Detect date column
        date_cols = [col for col in df.columns if "date" in col.lower()]
        if date_cols:
            df['Date'] = pd.to_datetime(
                df[date_cols[0]],
                errors='coerce',
                dayfirst=True
            )
        else:
            df['Date'] = pd.NaT

        # Detect description column
        desc_col = None
        for col in df.columns:
            if "desc" in col.lower() or "narration" in col.lower() or "details" in col.lower():
                desc_col = col
                break

        # Detect debit/credit columns if they exist
        debit_cols = [col for col in df.columns if "debit" in col.lower()]
        credit_cols = [col for col in df.columns if "credit" in col.lower()]

        total_debit, total_credit = 0, 0
        amount_col = None

        if debit_cols:
            total_debit = df[debit_cols[0]].sum(numeric_only=True)
            amount_col = debit_cols[0]

        if credit_cols:
            total_credit = df[credit_cols[0]].sum(numeric_only=True)
            amount_col = credit_cols[0]

        # 🔹 If no explicit debit/credit columns → auto classify using description
        if not debit_cols and not credit_cols and desc_col:
            df['Type'] = df[desc_col].astype(str).str.upper().apply(
                lambda x: "Credit" if any(word in x for word in ["BY", "CREDIT", "SALARY", "REFUND"]) 
                else ("Debit" if any(word in x for word in ["TO", "DEBIT", "TRANSFER", "WITHDRAWAL"]) 
                else "Other")
            )

            # Try to detect amount column (assume last numeric column)
            num_cols = df.select_dtypes(include="number").columns
            if len(num_cols) > 0:
                amount_col = num_cols[-1]  # pick last numeric column
                total_credit = df.loc[df['Type'] == "Credit", amount_col].sum()
                total_debit = df.loc[df['Type'] == "Debit", amount_col].sum()

                # Add Month column for grouping
                if 'Date' in df:
                    df['Month'] = df['Date'].dt.to_period("M").astype(str)

        # 📊 Analysis Section
        st.subheader("📊 Analysis")
        st.write("✅ Total Rows:", len(df))

        if 'Date' in df:
            st.write("📅 Date Range:", df['Date'].min(), "→", df['Date'].max())

        st.write("💰 Total Credit:", total_credit)
        st.write("💸 Total Debit:", total_debit)
        st.write("📌 Net Balance (Credit - Debit):", total_credit - total_debit)

        # 📈 Monthly Charts
        monthly = None
        if 'Month' in df and 'Type' in df and amount_col:
            monthly = df.groupby(['Month', 'Type'])[amount_col].sum().unstack().fillna(0)

            st.subheader("📈 Monthly Income vs Expense")

            fig, ax = plt.subplots(figsize=(8, 4))
            monthly.plot(kind='bar', ax=ax)
            ax.set_ylabel("Amount")
            ax.set_title("Monthly Income vs Expense")
            st.pyplot(fig)

        # 📥 Download Reports
        st.subheader("📥 Download Report")

        # Excel Export
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Raw Data", index=False)
            summary = pd.DataFrame({
                "Total Credit": [total_credit],
                "Total Debit": [total_debit],
                "Net Balance": [total_credit - total_debit]
            })
            summary.to_excel(writer, sheet_name="Summary", index=False)
            if monthly is not None:
                monthly.to_excel(writer, sheet_name="Monthly Analysis")
        excel_data = output.getvalue()

        st.download_button(
            label="📊 Download Excel Report",
            data=excel_data,
            file_name="Bank_Statement_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
