import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Tyco Logistics Platform", page_icon="🚛", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .main-title { text-align: center; color: #00ADB5; font-size: 35px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">Tyco VMI & Logistics Tracker</p>', unsafe_allow_html=True)

# Sidebar for Upload
with st.sidebar:
    st.header("Data Sources")
    uploaded_file = st.file_uploader("Upload Tyco Excel Report", type=['xlsx'])
    st.divider()
    st.info("System Status: Ready")

if uploaded_file:
    # Load Data
    try:
        df = pd.read_excel(uploaded_file)
        
        # Clean column names (remove leading/trailing spaces)
        df.columns = df.columns.str.strip()

        # Search Section
        st.markdown("### 🔍 Search Portal")
        col1, col2 = st.columns(2)
        
        with col1:
            tracking_search = st.text_input("Search by Tracking No:")
        
        with col2:
            material_search = st.text_input("Search by Material / PO:")

        # Filtering Logic
        filtered_df = df.copy()
        
        if tracking_search:
            # Search in all columns to ensure we catch the Tracking No
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(tracking_search, case=False)).any(axis=1)
            filtered_df = filtered_df[mask]
            
        if material_search:
            mask = filtered_df.astype(str).apply(lambda x: x.str.contains(material_search, case=False)).any(axis=1)
            filtered_df = filtered_df[mask]

        # Display Results
        st.markdown("---")
        st.subheader(f"Results: {len(filtered_df)} records found")
        st.dataframe(filtered_df, use_container_width=True)

        # Download Feature
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name='Tyco_Search_Report.csv',
                mime='text/csv',
            )

    except Exception as e:
        st.error(f"Error processing file: {e}")

else:
    st.warning("Please upload an Excel file to display the tracking dashboard.")
