import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Bank Statement Analyzer", layout="wide")

st.title("🏦 Bank Statement Analyzer (SBI Compatible)")

uploaded_file = st.file_uploader("Upload your Bank Statement (Excel)", type=["xls", "xlsx"])

if uploaded_file:
    try:
        # Load Excel
        df = pd.read_excel(uploaded_file)

        # Standardize column names for SBI format
        df.rename(columns={
            'Narration': 'Description',
            'Withdrawal Amt.': 'Debit',
            'Deposit Amt.': 'Credit',
            'Value Date': 'Date'
        }, inplace=True)

        # Show raw preview
        st.subheader("📊 Raw Data Preview")
        st.dataframe(df.head(10))

        # Check required columns
        required_cols = ['Date', 'Description', 'Debit', 'Credit']
        missing = [col for col in required_cols if col not in df.columns]

        if missing:
            st.error(f"Missing required columns: {', '.join(missing)}")
        else:
            # Clean debit/credit columns
            df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
            df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)

            # Convert Date
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Summary
            total_debit = df['Debit'].sum()
            total_credit = df['Credit'].sum()
            net_balance = total_credit - total_debit

            st.subheader("📌 Summary")
            st.write(f"💰 Total Credit: **{total_credit:,.2f}**")
            st.write(f"💸 Total Debit: **{total_debit:,.2f}**")
            st.write(f"📌 Net Balance (Credit - Debit): **{net_balance:,.2f}**")

            # Top spending categories
            st.subheader("📊 Top 5 Debit Transactions by Description")
            debit_by_desc = df.groupby('Description')['Debit'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(debit_by_desc)

            st.subheader("📊 Top 5 Credit Transactions by Description")
            credit_by_desc = df.groupby('Description')['Credit'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(credit_by_desc)

            # ==============================
            # PDF Report Download
            # ==============================
            def create_pdf(data, debit, credit, net):
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                elements = []

                elements.append(Paragraph("🏦 Bank Statement Report", styles['Title']))
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(f"💰 Total Credit: {credit:,.2f}", styles['Normal']))
                elements.append(Paragraph(f"💸 Total Debit: {debit:,.2f}", styles['Normal']))
                elements.append(Paragraph(f"📌 Net Balance: {net:,.2f}", styles['Normal']))
                elements.append(Spacer(1, 12))

                # Table
                table_data = [data.columns.tolist()] + data.values.tolist()
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)

                doc.build(elements)
                buffer.seek(0)
                return buffer

            pdf_buffer = create_pdf(df.head(50), total_debit, total_credit, net_balance)
            b64_pdf = base64.b64encode(pdf_buffer.read()).decode('utf-8')
            href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="Bank_Report.pdf">📥 Download Report</a>'
            st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Error reading file: {e}")
