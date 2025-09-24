import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Bank Statement Analyzer", layout="wide")

st.title("📊 Bank Statement Analyzer")

uploaded_file = st.file_uploader("Upload your Bank Statement (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file:
    # Read file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Show raw data
    st.subheader("📑 Raw Data Preview")
    st.dataframe(df.head(20))

    # 🔹 Auto-detect columns
    col_map = {}
    for col in df.columns:
        c = col.strip().lower()

        if "date" in c:
            col_map[col] = "Date"
        elif any(x in c for x in ["withdrawal", "debit", "outflow", "spent", "paid"]):
            col_map[col] = "Debit"
        elif any(x in c for x in ["deposit", "credit", "inflow", "received", "income"]):
            col_map[col] = "Credit"
        elif "desc" in c or "narration" in c or "remarks" in c:
            col_map[col] = "Description"
        elif "balance" in c:
            col_map[col] = "Balance"
        elif "ref" in c or "cheque" in c:
            col_map[col] = "Ref_No"

    df.rename(columns=col_map, inplace=True)

    # Ensure required columns
    if 'Date' not in df.columns:
        st.error("❌ No 'Date' column found. Please check your file.")
    else:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        if 'Debit' not in df.columns:
            df['Debit'] = 0
        if 'Credit' not in df.columns:
            df['Credit'] = 0

        df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
        df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)

        # 🔹 Analysis
        st.subheader("📊 Analysis")
        st.write("✅ Total Rows:", len(df))

        date_min, date_max = df['Date'].min(), df['Date'].max()
        st.write("📅 Date Range:", date_min, "→", date_max)

        total_credit = df['Credit'].sum()
        total_debit = df['Debit'].sum()
        net_balance = total_credit - total_debit

        st.write("💰 Total Credit:", f"{total_credit:,.2f}")
        st.write("💸 Total Debit:", f"{total_debit:,.2f}")
        st.write("📌 Net Balance (Credit - Debit):", f"{net_balance:,.2f}")

        # 🔹 Monthly Summary
        df['Month'] = df['Date'].dt.to_period('M')
        monthly_summary = df.groupby('Month')[['Debit', 'Credit']].sum().reset_index()
        monthly_summary['Month'] = monthly_summary['Month'].astype(str)

        st.subheader("📅 Monthly Summary")
        st.dataframe(monthly_summary)

        # 🔹 Graphs
        st.subheader("📈 Visual Insights")

        # Daily trend chart
        fig, ax = plt.subplots(figsize=(8, 4))
        df.groupby('Date')[['Debit', 'Credit']].sum().plot(ax=ax)
        plt.title("Daily Debit & Credit Trend")
        plt.ylabel("Amount")
        st.pyplot(fig)

        # Save daily trend for PDF
        img_buffer1 = io.BytesIO()
        fig.savefig(img_buffer1, format='png')
        img_buffer1.seek(0)

        # Monthly bar chart
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        monthly_summary.plot(x='Month', y=['Debit', 'Credit'], kind='bar', ax=ax3)
        plt.title("Monthly Debit & Credit Summary")
        plt.ylabel("Amount")
        st.pyplot(fig3)

        img_buffer2 = io.BytesIO()
        fig3.savefig(img_buffer2, format='png')
        img_buffer2.seek(0)

        # Pie chart
        fig2, ax2 = plt.subplots()
        debit_by_desc = df.groupby('Description')['Debit'].sum().sort_values(ascending=False).head(5)
        debit_by_desc.plot.pie(ax=ax2, autopct='%1.1f%%', startangle=90)
        plt.title("Top 5 Spending Categories")
        st.pyplot(fig2)

        img_buffer3 = io.BytesIO()
        fig2.savefig(img_buffer3, format='png')
        img_buffer3.seek(0)

        # 🔹 Download Excel Report
        st.subheader("📥 Download Reports")

        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Raw Data", index=False)

            summary = pd.DataFrame({
                "Metric": ["Total Credit", "Total Debit", "Net Balance"],
                "Value": [total_credit, total_debit, net_balance]
            })
            summary.to_excel(writer, sheet_name="Summary", index=False)

            monthly_summary.to_excel(writer, sheet_name="Monthly Summary", index=False)

        st.download_button(
            "⬇ Download Excel Report",
            data=output_excel.getvalue(),
            file_name="Bank_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 🔹 Download PDF Report
        output_pdf = io.BytesIO()
        doc = SimpleDocTemplate(output_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("📊 Bank Statement Analysis Report", styles["Title"]))
        elements.append(Spacer(1, 12))

        # Summary table
        data = [["Metric", "Value"],
                ["Total Credit", f"{total_credit:,.2f}"],
                ["Total Debit", f"{total_debit:,.2f}"],
                ["Net Balance", f"{net_balance:,.2f}"]]

        table = Table(data, colWidths=[150, 150])
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                                   ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                                   ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                   ("GRID", (0, 0), (-1, -1), 1, colors.black)]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # Insert charts into PDF
        elements.append(Paragraph("Daily Debit & Credit Trend", styles["Heading2"]))
        elements.append(Image(img_buffer1, width=400, height=200))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Monthly Debit & Credit Summary", styles["Heading2"]))
        elements.append(Image(img_buffer2, width=400, height=200))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph("Top 5 Spending Categories", styles["Heading2"]))
        elements.append(Image(img_buffer3, width=300, height=200))
        elements.append(Spacer(1, 12))

        doc.build(elements)

        st.download_button(
            "⬇ Download PDF Report",
            data=output_pdf.getvalue(),
            file_name="Bank_Report.pdf",
            mime="application/pdf"
        )
