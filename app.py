import streamlit as st
import pandas as pd
import os
import io

# App Configuration
st.set_page_config(page_title="Tyco Logistics System", layout="wide")

MASTER_DB = "Tyco_Master_Database.csv"
SEP = ";"  # Matches your Excel settings

def load_master_data():
    if os.path.exists(MASTER_DB):
        try:
            # We try to read with the defined separator
            df = pd.read_csv(MASTER_DB, sep=SEP)
            # Standardize columns: Strip spaces and fix common Tyco naming issues
            df.columns = df.columns.str.strip()
            if 'PGI Date' in df.columns:
                df['PGI Date'] = pd.to_datetime(df['PGI Date'], errors='coerce')
            return df
        except Exception as e:
            st.error(f"Error reading Database: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# 1. Sidebar
with st.sidebar:
    st.header("📦 Data Management")
    master_df_sidebar = load_master_data()
    
    if not master_df_sidebar.empty:
        st.metric("Total Records", len(master_df_sidebar))
        # Export logic remains same...
    
    st.divider()
    uploaded_file = st.file_uploader("Upload Daily Sheet", type=['xlsx', 'xls'])
    
    if uploaded_file:
        if st.button("Process & Save"):
            new_data = pd.read_excel(uploaded_file, engine='openpyxl')
            new_data.columns = new_data.columns.str.strip() # Clean headers immediately
            
            master_df = load_master_data()
            combined_df = pd.concat([master_df, new_data], ignore_index=True)
            
            # Use 'ShipmntNbr' safely
            if 'ShipmntNbr' in combined_df.columns:
                combined_df.drop_duplicates(subset=['ShipmntNbr', 'Dely No'], keep='last', inplace=True)
            else:
                combined_df.drop_duplicates(inplace=True)
                
            combined_df.to_csv(MASTER_DB, index=False, sep=SEP, encoding='utf-8-sig')
            st.success("Database Updated!")
            st.rerun()

# 2. Main Interface
st.title("Tyco Logistics Engine 🚀")
raw_df = load_master_data()

if not raw_df.empty:
    # --- DEBUGGING SECTION ---
    # This helps you see what columns Python actually sees
    if st.checkbox("Debug: Show Column Names"):
        st.write("Current Columns in File:", list(raw_df.columns))

    st.subheader("🔍 Search Filters")
    c1, c2, c3, c4 = st.columns(4)
    
    # SAFE SEARCH LOGIC
    # We check if the column exists before trying to filter it
    ship_in = c1.text_input("Shipment No")
    track_in = c2.text_input("Tracking No")
    mat_in = c3.text_input("Material Nbr")
    dely_in = c4.text_input("Delivery No")

    filtered_df = raw_df.copy()
    
    # Applying filters ONLY if column exists and input is provided
    col_map = {
        'ShipmntNbr': ship_in,
        'Tracking No': track_in,
        'Cust Material Nbr': mat_in,
        'Dely No': dely_in
    }

    for col, val in col_map.items():
        if val and col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, na=False, case=False)]

    # 3. Summarization
    group_cols = ['ShipmntNbr', 'Tracking No', 'Cust Material Nbr', 'Dely No']
    # Only group by columns that actually exist in the file
    valid_group_cols = [c for c in group_cols if c in filtered_df.columns]

    if not filtered_df.empty and valid_group_cols:
        if 'Dely Qty' in filtered_df.columns:
            filtered_df['Dely Qty'] = pd.to_numeric(filtered_df['Dely Qty'], errors='coerce').fillna(0)
            
            summary_df = filtered_df.groupby(valid_group_cols, as_index=False).agg({
                'Dely Qty': 'sum',
                'Shipto City': 'first' if 'Shipto City' in filtered_df.columns else 'last',
                'PGI Date': 'max' if 'PGI Date' in filtered_df.columns else 'last'
            })
            
            st.dataframe(summary_df, use_container_width=True)
        else:
            st.warning("Column 'Dely Qty' not found in the uploaded data.")
            st.dataframe(filtered_df)
else:
    st.info("Please upload a file to start.")
