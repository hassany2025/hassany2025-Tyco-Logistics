import streamlit as st
import pandas as pd
import os
import io

# 1. App Configuration
st.set_page_config(page_title="Tyco Logistics System", layout="wide")

# Constants for your environment
MASTER_DB = "Tyco_Master_Database.csv"
SEP = ";"  # Matches your Excel (Semicolon separator) settings

def load_master_data():
    """Loads and cleans the master database."""
    if os.path.exists(MASTER_DB):
        try:
            df = pd.read_csv(MASTER_DB, sep=SEP, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            if 'PGI Date' in df.columns:
                df['PGI Date'] = pd.to_datetime(df['PGI Date'], dayfirst=True, errors='coerce')
            return df
        except Exception as e:
            st.error(f"Error reading Database: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# --- SIDEBAR: Data Management ---
with st.sidebar:
    st.header("📦 Data Management")
    
    current_db = load_master_data()
    if not current_db.empty:
        st.metric("Total History Records", len(current_db))
        
        # Backup Logic
        buffer_all = io.BytesIO()
        with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
            current_db.to_excel(writer, index=False, sheet_name='Full_History')
        st.download_button("📥 Download Full History", buffer_all.getvalue(), "Full_Tyco_History.xlsx")

    st.divider()
    
    uploaded_file = st.file_uploader("Upload Daily Sheet (Excel)", type=['xlsx'])
    if uploaded_file:
        if st.button("🚀 Process & Store Data"):
            new_data = pd.read_excel(uploaded_file)
            new_data.columns = new_data.columns.str.strip()
            
            # Combine current database with new upload
            combined_df = pd.concat([current_db, new_data], ignore_index=True)
            
            # Smart Deduplication: Keep the latest update
            keys = ['ShipmntNbr', 'Dely No', 'Cust Material Nbr']
            existing_keys = [c for c in keys if c in combined_df.columns]
            combined_df.drop_duplicates(subset=existing_keys, keep='last', inplace=True)
            
            combined_df.to_csv(MASTER_DB, index=False, sep=SEP, encoding='utf-8-sig')
            st.success("Database Updated Successfully!")
            st.rerun()

    if st.checkbox("Advanced: Clear Database"):
        if st.button("⚠️ Wipe All Data"):
            if os.path.exists(MASTER_DB):
                os.remove(MASTER_DB)
                st.warning("All records deleted.")
                st.rerun()

# --- MAIN INTERFACE: Search & The Quantities Rule ---
st.title("Tyco Logistics Engine 🚀")
raw_df = load_master_data()

if not raw_df.empty:
    st.subheader("🔍 Search & Summarized Report")
    
    # Search Filters
    c1, c2, c3, c4 = st.columns(4)
    ship_in = c1.text_input("Shipment No")
    track_in = c2.text_input("Tracking No")
    mat_in = c3.text_input("Material Nbr")
    dely_in = c4.text_input("Delivery No") # السطر اللي كان فيه المشكلة اتصلح هنا

    # Filtering Logic
    filtered_df = raw_df.copy()
    filter_map = {
        'ShipmntNbr': ship_in,
        'Tracking No': track_in,
        'Cust Material Nbr': mat_in,
        'Dely No': dely_in
    }

    for col, val in filter_map.items():
        if val and col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, na=False, case=False)]

    # --- 2. APPLY THE SUMMARIZATION RULE ---
    group_cols = ['ShipmntNbr', 'Tracking No', 'Cust Material Nbr', 'Dely No']
    valid_group_cols = [c for c in group_cols if c in filtered_df.columns]
    
    if not filtered_df.empty and valid_group_cols:
        if 'Dely Qty' in filtered_df.columns:
            filtered_df['Dely Qty'] = pd.to_numeric(filtered_df['Dely Qty'], errors='coerce').fillna(0)
            
            agg_rules = {'Dely Qty': 'sum'}
            if 'Shipto City' in filtered_df.columns: agg_rules['Shipto City'] = 'first'
            if 'PGI Date' in filtered_df.columns: agg_rules['PGI Date'] = 'max'
            
            summary_df = filtered_df.groupby(valid_group_cols, as_index=False).agg(agg_rules)
            summary_df = summary_df[summary_df['Dely Qty'] > 0] # استبعاد الكميات الصفرية
            
            st.write(f"### Results Found: {len(summary_df)}")
            display_df = summary_df.copy()
            if 'PGI Date' in display_df.columns:
                display_df['PGI Date'] = display_df['PGI Date'].dt.strftime('%d/%m/%Y')
            
            st.dataframe(display_df, use_container_width=True)

            # Export Logic
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                summary_df.to_excel(writer, index=False, sheet_name='Summarized_Report')
            
            st.download_button("📥 Download Summarized Excel", buffer.getvalue(), "Tyco_Summary.xlsx")
        else:
            st.error("Column 'Dely Qty' not found.")
else:
    st.info("The database is currently empty. Please upload a file from the sidebar.")
