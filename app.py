import streamlit as st
import pandas as pd
import os
import io

# App Configuration
st.set_page_config(page_title="Tyco Logistics System", layout="wide")

# Using semicolon separator to match your Excel system settings
MASTER_DB = "Tyco_Master_Database.csv"
SEP = ";" 

def load_master_data():
    """Reads the master database and handles PGI date formatting."""
    if os.path.exists(MASTER_DB):
        df = pd.read_csv(MASTER_DB, sep=SEP)
        if 'PGI Date' in df.columns:
            df['PGI Date'] = pd.to_datetime(df['PGI Date'], errors='coerce')
        return df
    return pd.DataFrame()

# 1. Sidebar - Data Management
with st.sidebar:
    st.header("📦 Data Management")
    
    # Live stats from the database
    master_df_sidebar = load_master_data()
    if not master_df_sidebar.empty:
        st.metric("Total Records in DB", len(master_df_sidebar))
        
        # --- FULL BACKUP SECTION ---
        st.subheader("Full Database Export")
        export_all_df = master_df_sidebar.copy()
        if 'PGI Date' in export_all_df.columns:
            export_all_df['PGI Date'] = export_all_df['PGI Date'].dt.strftime('%d/%m/%Y')
            
        buffer_all = io.BytesIO()
        with pd.ExcelWriter(buffer_all, engine='xlsxwriter') as writer:
            export_all_df.to_excel(writer, index=False, sheet_name='Full_Master_History')
        
        st.download_button(
            label="📥 Download Full Backup (Excel)",
            data=buffer_all.getvalue(),
            file_name=f"Tyco_Full_History_{pd.Timestamp.now().strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.divider()
    
    # Uploading new daily sheets
    uploaded_file = st.file_uploader("Upload New Daily Sheet", type=['xlsx', 'xls'])
    if uploaded_file:
        if st.button("Process & Save to Master"):
            new_data = pd.read_excel(uploaded_file, engine='openpyxl')
            new_data.columns = new_data.columns.str.strip() # Clean column names
            
            master_df = load_master_data()
            combined_df = pd.concat([master_df, new_data], ignore_index=True)
            
            # Smart deduplication: Keep the latest update for each Delivery
            if 'Dely No' in combined_df.columns:
                combined_df.drop_duplicates(subset=['ShipmntNbr', 'Dely No', 'Cust Material Nbr'], keep='last', inplace=True)
            else:
                combined_df.drop_duplicates(inplace=True)
            
            combined_df.to_csv(MASTER_DB, index=False, sep=SEP, encoding='utf-8-sig')
            st.success("Database Updated Successfully!")
            st.rerun()

    if st.checkbox("Show Advanced Tools"):
        if st.button("⚠️ Wipe Database"):
            if os.path.exists(MASTER_DB):
                os.remove(MASTER_DB)
                st.warning("All records deleted.")
                st.rerun()

# 2. Main Interface - Search & Reporting
st.title("Tyco Logistics Search Engine 🚀")
raw_df = load_master_data()

if not raw_df.empty:
    # Search Filters
    st.subheader("🔍 Shipment Tracking")
    c1, c2, c3, c4 = st.columns(4)
    with c1: ship_in = st.text_input("Shipment No")
    with c2: track_in = st.text_input("Tracking No")
    with c3: mat_in = st.text_input("Material Nbr")
    with c4: dely_in = st.text_input("Delivery No")

    # Filter Logic
    filtered_df = raw_df.copy()
    if ship_in: filtered_df = filtered_df[filtered_df['ShipmntNbr'].astype(str).str.contains(ship_in, na=False)]
    if track_in: filtered_df = filtered_df[filtered_df['Tracking No'].astype(str).str.contains(track_in, na=False)]
    if mat_in: filtered_df = filtered_df[filtered_df['Cust Material Nbr'].astype(str).str.contains(mat_in, na=False)]
    if dely_in: filtered_df = filtered_df[filtered_df['Dely No'].astype(str).str.contains(dely_in, na=False)]

    # 3. Summarization Rule (The Logic)
    group_cols = ['ShipmntNbr', 'Tracking No', 'Cust Material Nbr', 'Dely No']
    available_cols = [c for c in group_cols if c in filtered_df.columns]
    
    if not filtered_df.empty and len(available_cols) == len(group_cols):
        filtered_df['Dely Qty'] = pd.to_numeric(filtered_df['Dely Qty'], errors='coerce').fillna(0)
        
        summary_df = filtered_df.groupby(group_cols, as_index=False).agg({
            'Dely Qty': 'sum',
            'Shipto City': 'first',
            'PGI Date': 'max'
        })
        summary_df = summary_df[summary_df['Dely Qty'] > 0]
        
        st.info(f"Showing {len(summary_df)} unique records based on your search.")
        
        # Date Display Formatting
        display_df = summary_df.copy()
        if 'PGI Date' in display_df.columns:
            display_df['PGI Date'] = display_df['PGI Date'].dt.strftime('%d/%m/%Y')
        
        st.dataframe(display_df, use_container_width=True)

        # 4. Download Summarized Report
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            summary_df.to_excel(writer, index=False, sheet_name='Search_Results')
            
        st.download_button(
            label="📥 Download Search Results (Excel)",
            data=buffer.getvalue(),
            file_name="Tyco_Search_Results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.warning("System is ready. Please upload a file from the sidebar to begin.")
