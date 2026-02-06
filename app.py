import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Tyco Logistics Search", page_icon="🚛", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #00ADB5; font-size: 32px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">Tyco Advanced Logistics Search</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Upload Center")
    uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx'])
    st.divider()
    st.info("Logistics Management System v3.0")

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        # Standardize column names
        df.columns = df.columns.str.strip()

        # --- Search Boxes Section ---
        st.markdown("### 🔍 Search Filters")
        
        # Creating 4 columns for the 4 search boxes
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            dely_search = st.text_input("Dely No")
        with col2:
            cust_mat_search = st.text_input("Cust Material Nbr")
        with col3:
            track_search = st.text_input("Tracking No")
        with col4:
            ship_search = st.text_input("ShipmntNbr")

        # Filtering Logic
        filtered_df = df.copy()

        # Apply filters only if input is provided
        if dely_search:
            filtered_df = filtered_df[filtered_df.astype(str).apply(lambda x: x.str.contains(dely_search, case=False)).any(axis=1) if 'Dely No' not in df.columns else filtered_df['Dely No'].astype(str).str.contains(dely_search, case=False)]
        
        if cust_mat_search:
            filtered_df = filtered_df[filtered_df.astype(str).apply(lambda x: x.str.contains(cust_mat_search, case=False)).any(axis=1) if 'Cust Material Nbr' not in df.columns else filtered_df['Cust Material Nbr'].astype(str).str.contains(cust_mat_search, case=False)]
            
        if track_search:
            filtered_df = filtered_df[filtered_df.astype(str).apply(lambda x: x.str.contains(track_search, case=False)).any(axis=1) if 'Tracking No' not in df.columns else filtered_df['Tracking No'].astype(str).str.contains(track_search, case=False)]
            
        if ship_search:
            filtered_df = filtered_df[filtered_df.astype(str).apply(lambda x: x.str.contains(ship_search, case=False)).any(axis=1) if 'ShipmntNbr' not in df.columns else filtered_df['ShipmntNbr'].astype(str).str.contains(ship_search, case=False)]

        # Results Area
        st.markdown("---")
        st.subheader(f"Records Found: {len(filtered_df)}")
        st.dataframe(filtered_df, use_container_width=True)

        # Download Button
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Export Search Results",
                data=csv,
                file_name='Filtered_Tyco_Report.csv',
                mime='text/csv',
            )

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("Please upload the Tyco Logistics Excel file to enable search filters.")
