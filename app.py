import streamlit as st
import pandas as pd
import os
import io

# 1. App Configuration
st.set_page_config(page_title="Tyco Logistics System", layout="wide")

# Constants for your specific environment
MASTER_DB = "Tyco_Master_Database.csv"
SEP = ";"  # Matches your Excel (Semicolon separator) settings

def load_master_data():
    """Loads and cleans the master database."""
    if os.path.exists(MASTER_DB):
        try:
            df = pd.read_csv(MASTER_DB, sep=SEP, encoding='utf-8-sig')
            df.columns = df.columns.str.strip() # Remove hidden spaces
            if 'PGI Date' in df.columns:
                df['PGI Date'] = pd.to_datetime(df['PGI Date'], dayfirst=True, errors='coerce')
            return df
        except Exception as e:
            st.error(f"Error reading Database: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# --- SIDEBAR: Data Management & Storage ---
with st.sidebar:
    st.header("📦 Data Management")
    
    # Show current DB status
    current_db = load_master_data()
    if not current_db.empty:
        st.metric("Total Records in History", len(current_db))
        
        # Backup Button
        buffer_all = io.BytesIO()
        with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
            current_db.to_excel(writer, index=False, sheet_name='Full_History')
        st.download_button("📥 Download Full History", buffer_all.getvalue(), "Full_Tyco_History.xlsx")

    st.divider()
    
    # Upload Daily Sheet
    uploaded_file = st.file_uploader("Upload Daily Sheet (Excel)", type=['xlsx'])
    if uploaded_file:
        if st.button("🚀 Process & Store Data"):
            new_data = pd.read_excel(uploaded_file)
            new_data.columns = new_data.columns.str.strip() # Clean headers
            
            # Combine current database with new upload (Tomorrow's data logic)
            combined_df = pd.concat([current_db, new_data], ignore_index=True)
            
            # --- SMART DEDUPLICATION ---
            # If same Shipment, Delivery, and Material exist, keep only the latest update
            keys = ['ShipmntNbr', 'Dely No', 'Cust Material Nbr']
            existing_keys = [c for c in keys if c in combined_df.columns]
            combined_df.drop_duplicates(subset=existing_keys, keep='last', inplace=True)
            
            # Save to CSV using semicolon for your Excel settings
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
    
    # 1. Search Filters
    c1, c2, c3, c4 = st.columns(4)
    ship_in = c1.text_input("Shipment No")
    track_in = c2.text_input("Tracking No")
    mat_in = c3.text_input("Material Nbr")
    dely_in = c4.text_input("
