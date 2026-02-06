import streamlit as st
import pandas as pd
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Tyco VMI Platform", page_icon="🚛", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-header { font-size: 30px; font-weight: bold; color: #00ADB5; }
    .card { background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4F4F4F; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file)
        # Fix format
        cols_to_str = ['SO No', 'PO Number', 'Material Number', 'ShipmntNbr', 'Tracking No']
        for col in cols_to_str:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
        
        if 'PGI Date' in df.columns:
            df['PGI Date'] = pd.to_datetime(df['PGI Date'], errors='coerce').dt.strftime('%d/%m/%Y')
        
        # Auto Status
        if 'Status' not in df.columns:
            df['Status'] = df['PGI Date'].apply(lambda x: 'Shipped 🚀' if pd.notnull(x) and x != '' else 'Pending ⏳')

        return df.fillna("-")
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏭 Tyco VMI")
    uploaded_file = st.file_uploader("📂 Upload Excel", type=["xlsx"])
    st.info("System Ready")

# --- MAIN PAGE ---
st.markdown('<p class="main-header">🚛 Logistics Tracking Platform</p>', unsafe_allow_html=True)

if uploaded_file:
    df = load_data(uploaded_file)
    if df is not None:
        tab1, tab2 = st.tabs(["📊 Dashboard", "🔎 Search"])
        
        with tab1:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Shipments", len(df))
            c2.metric("Shipped", len(df[df['Status'].str.contains('Shipped')]))
            total_qty = pd.to_numeric(df['Dely Qty'], errors='coerce').sum() if 'Dely Qty' in df.columns else 0
            c3.metric("Total Qty", f"{total_qty:,.0f}")
            st.dataframe(df, use_container_width=True)

        with tab2:
            c1, c2, c3 = st.columns(3)
            f_ship = c1.text_input("Shipment Num")
            f_po = c2.text_input("PO Num")
            f_mat = c3.text_input("Material Num")
            
            df_f = df.copy()
            if f_ship: df_f = df_f[df_f['ShipmntNbr'].str.contains(f_ship, case=False)]
            if f_po: df_f = df_f[df_f['PO Number'].str.contains(f_po, case=False)]
            if f_mat: df_f = df_f[df_f['Material Number'].str.contains(f_mat, case=False)]
            
            st.dataframe(df_f, use_container_width=True)
else:
    st.info("👋 Upload Data to start.")
