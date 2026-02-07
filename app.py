import streamlit as st
import pandas as pd
import os
import io

# App Configuration
st.set_page_config(page_title="Tyco Logistics Search", layout="wide")

MASTER_DB = "Tyco_Master_Database.csv"

def load_master_data():
    if os.path.exists(MASTER_DB):
        return pd.read_csv(MASTER_DB)
    return pd.DataFrame()

# 1. Sidebar for File Upload & Processing
with st.sidebar:
    st.header("Data Management")
    uploaded_file = st.file_uploader("Upload Daily Sheet", type=['xlsx', 'xls'])
    
    if uploaded_file:
        if st.button("Save to Master Database"):
            new_data = pd.read_excel(uploaded_file, engine='openpyxl')
            master_df = load_master_data()
            
            combined_df = pd.concat([master_df, new_data], ignore_index=True)
            
            # Remove duplicates based on Delivery Number
            if 'Dely No' in combined_df.columns:
                combined_df.drop_duplicates(subset=['Dely No'], keep='last', inplace=True)
            
            combined_df.to_csv(MASTER_DB, index=False)
            st.success("Database Updated Successfully!")

# 2. Main Interface - Search Filters
st.title("Tyco Advanced Logistics Search")
st.subheader("🔍 Search Filters")

df = load_master_data()

if not df.empty:
    # Creating search columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        dely_in = st.text_input("Dely No")
    with col2:
        mat_in = st.text_input("Cust Material Nbr")
    with col3:
        track_in = st.text_input("Tracking No")
    with col4:
        ship_in = st.text_input("ShipmntNbr")

    # Filtering Logic
    filtered_df = df.copy()
    
    if dely_in:
        filtered_df = filtered_df[filtered_df['Dely No'].astype(str).str.contains(dely_in, case=False, na=False)]
    if mat_in:
        filtered_df = filtered_df[filtered_df['Cust Material Nbr'].astype(str).str.contains(mat_in, case=False, na=False)]
    if track_in:
        filtered_df = filtered_df[filtered_df['Tracking No'].astype(str).str.contains(track_in, case=False, na=False)]
    if ship_in:
        filtered_df = filtered_df[filtered_df['ShipmntNbr'].astype(str).str.contains(ship_in, case=False, na=False)]

    # 3. Display Results
    st.divider()
    st.write(f"### Records Found: {len(filtered_df)}")
    st.dataframe(filtered_df, use_container_width=True)

    # 4. Export logic with custom column names
    if not filtered_df.empty:
        # Mapping columns to match your image
        rename_map = {
            'ShipmntNbr': 'Shipment No',
            'Shipto City': 'Ship to City',
            'Tracking No': 'Tracking No',
            'Cust Material Nbr': 'Cust Material N',
            'Dely Qty': 'Dely Qt',
            'Dely No': 'Dely No',
            'PGI Date': 'PGI Date'
        }
        
        export_df = filtered_df.rename(columns=rename_map)
        
        # Ensure only requested columns are exported (and in order)
        final_cols = ['Shipment No', 'Ship to City', 'Tracking No', 'Cust Material N', 'Dely Qt', 'Dely No', 'PGI Date']
        export_df = export_df[[c for c in final_cols if c in export_df.columns]]

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Tyco_Report')
            
            # Formatting Date Column and Design
            workbook  = writer.book
            worksheet = writer.sheets['Tyco_Report']
            
            # Date format: dd/mm/yyyy
            date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            
            # Apply format to Column G (PGI Date)
            worksheet.set_column('G:G', 15, date_fmt)
            
            # Bold Header Format
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            for col_num, value in enumerate(export_df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)

        st.download_button(
            label="📥 Download Results as Excel",
            data=buffer.getvalue(),
            file_name="Tyco_Formatted_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("The database is currently empty. Please upload a file from the sidebar to start.")
