import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Bank Statement Analyzer - Multi-Bank")

uploaded_files = st.file_uploader(
    "Upload one or more CSV/XLSX files",
    type=['csv','xlsx'],
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []
    for uploaded_file in uploaded_files:
        # Read file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        dfs.append(df)
    
    df = pd.concat(dfs, ignore_index=True)

    # ===== Auto-detect columns =====
    credit_cols = [c for c in df.columns if 'credit' in c.lower() or 'received' in c.lower() or 'deposit' in c.lower()]
    debit_cols = [c for c in df.columns if 'debit' in c.lower() or 'paid' in c.lower() or 'withdraw' in c.lower()]
    date_cols = [c for c in df.columns if 'date' in c.lower()]
    desc_cols = [c for c in df.columns if 'desc' in c.lower() or 'particular' in c.lower() or 'narration' in c.lower()]

    # Assign detected columns or default
    df['Credit'] = df[credit_cols[0]] if credit_cols else 0
    df['Debit'] = df[debit_cols[0]] if debit_cols else 0
    df['Date'] = pd.to_datetime(df[date_cols[0]]) if date_cols else pd.NaT
    df['Description'] = df[desc_cols[0]] if desc_cols else ''

    # Convert to numeric
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)

    # ===== Calculations =====
    total_income = df['Credit'].sum()
    total_expense = df['Debit'].sum()
    total_savings = total_income - total_expense

    st.subheader("Summary")
    st.write(f"💰 Total Income: ₹{total_income:,.2f}")
    st.write(f"💸 Total Expenses: ₹{total_expense:,.2f}")
    st.write(f"📊 Total Savings: ₹{total_savings:,.2f}")

    # ===== Categorize expenses =====
    categories = {
        'Rent': ['rent','house'],
        'Food': ['restaurant','cafe','dining','dominos'],
        'Shopping': ['amazon','flipkart','store'],
        'Transport': ['ola','uber','fuel','bus','metro','taxi'],
        'Bills': ['electricity','water','internet','bill','mobile']
    }
    def categorize(desc):
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw.lower() in str(desc).lower():
                    return cat
        return 'Other'

    df['Category'] = df['Description'].apply(categorize)
    expense_summary = df.groupby('Category')['Debit'].sum()
    
    st.subheader("Expenses by Category")
    st.bar_chart(expense_summary)

    # ===== Downloadable report =====
    summary_df = pd.DataFrame({
        'Total Income':[total_income],
        'Total Expenses':[total_expense],
        'Total Savings':[total_savings]
    })
    summary_file = "Bank_Report.xlsx"
    summary_df.to_excel(summary_file, index=False)
    st.download_button("⬇️ Download Excel Report", summary_file)

    # ===== Preview uploaded data =====
    st.subheader("Preview of your transactions")
    st.write(df.head())
