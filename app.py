import streamlit as st
import pandas as pd
import os
import io

# App Configuration
st.set_page_config(page_title="Tyco Logistics Search", layout="wide")

MASTER_DB = "Tyco_Master_Database.csv"

def load_master_data():
    """Loads the raw master database."""
    if os.path.exists(MASTER_DB):
        df = pd.read_csv(MASTER_DB)
        if 'PGI Date' in df.columns:
            df['PGI Date'] = pd.to_datetime(df['PGI Date'], errors='coerce')
        return df
    return pd.DataFrame()

# 1. Sidebar - Data Ingestion (Storage Logic)
with st.sidebar:
    st.header("Data Management")
    uploaded_file = st.file_uploader("Upload Daily Sheet", type=['xlsx', 'xls'])
    
    if uploaded_file:
        if st.button("Save to Master Database"):
            new_data = pd.read_excel(uploaded_file, engine='openpyxl')
            raw_master = load_master_data()
            
            # Pure Raw Concatenation
            combined_raw = pd.concat([raw_master, new_data], ignore_index=True)
            
            # Remove only 100% identical rows (Safe Deduplication)
            combined_raw.drop_duplicates(inplace=True)
            
            combined_raw.to_csv(MASTER_DB, index=False)
            st.success("Raw Data Stored Safely!")

    st.divider()
    if st.checkbox("Advanced Options"):
        if st.button("⚠️ Reset Database"):
            if os.path.exists(MASTER_DB):
                os.remove(MASTER_DB)
                st.warning("Database cleared.")
                st.rerun()

# 2. Main Interface - The Search Engine
st.title("Tyco Advanced Logistics Search")
st.subheader("🔍 Shipment Search Engine")

raw_df = load_master_data()

if not raw_df.empty:
    # Search Inputs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ship_in = st.text_input("Shipment No")
    with col2:
        track_in = st.text_input("Tracking No")
    with col3:
        mat_in = st.text_input("Material Nbr")
    with col4:
        dely_in = st.text_input("Delivery No")

    # Filtering the Raw Data first
    working_df = raw_df.copy()
    if ship_in:
        working_df = working_df[working_df['ShipmntNbr'].astype(str).str.contains(ship_in, na=False)]
    if track_in:
        working_df = working_df[working_df['Tracking No'].astype(str).str.contains(track_in, na=False)]
    if mat_in:
        working_df = working_df[working_df['Cust Material Nbr'].astype(str).str.contains(mat_in, na=False)]
    if dely_in:
        working_df = working_df[working_df['Dely No'].astype(str).str.contains(dely_in, na=False)]

    # --- THE ACCOUNTING RULES (Observation #1 & #2) ---
    
    # A. Ensure Numeric & Filter Zeros BEFORE GroupBy (Cleaner Logic)
    working_df['Dely Qty'] = pd.to_numeric(working_df['Dely Qty'], errors='coerce').fillna(0)
    working_df = working_df[working_df['Dely Qty'] > 0] # Filter first!

    # B. Define Grouping Pillars (Pillar-based security)
    group_pillars = ['ShipmntNbr', 'Tracking No', 'Cust Material Nbr', 'Dely No']
    
    if not working_df.empty:
        # C. Generate the Summary (Accounting Logic)
        summary_df = working_df.groupby(group_pillars, as_index=False).agg({
            'Dely Qty': 'sum',           # Summing is now 100% safe
            'Shipto City': 'first',
            'PGI Date': 'max'
        })
    else:
        summary_df = working_df

    # 3. Display Results
    st.divider()
    st.write(f"### Records Found: {len(summary_df)}")
    
    # Presentation View (Formatting for web only)
    view_df = summary_df.copy()
    if 'PGI Date' in view_df.columns:
        view_df['PGI Date'] = view_df['PGI Date'].dt.strftime('%d/%m/%Y')

    st.dataframe(view_df, use_container_width=True)

    # 4. Export Logic (Matching Summary View)
    if not summary_df.empty:
        rename_map = {
            'ShipmntNbr': 'Shipment No', 'Shipto City': 'Ship to City',
            'Tracking No': 'Tracking No', 'Cust Material Nbr': 'Cust Material N',
            'Dely Qty': 'Dely Qt', 'Dely No': 'Dely No', 'PGI Date': 'PGI Date'
        }
        export_df = summary_df.rename(columns=rename_map)
        
        final_cols = ['Shipment No', 'Ship to City', 'Tracking No', 'Cust Material N', 'Dely Qt', 'Dely No', 'PGI Date']
        export_df = export_df[[c for c in final_cols if c in export_df.columns]]

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Tyco_Report')
            workbook = writer.book
            worksheet = writer.sheets['Tyco_Report']
            
            # Accounting style formatting
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            for col_num, value in enumerate(export_df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)
            
            # Adjust column width
            for i, col in enumerate(export_df.columns):
                column_len = max(export_df[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)

        st.download_button(
            label="📥 Download Summarized Excel Report",
            data=buffer.getvalue(),
            file_name="Tyco_Summarized_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("No data found. Please use the sidebar to upload files.")
