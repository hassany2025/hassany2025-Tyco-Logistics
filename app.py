"""
Tyco Logistics Engine
---------------------
Developed by: Eng-Ahmed Hassany
Internal Use Only
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from pathlib import Path

# ================= CONFIG =================
st.set_page_config(page_title="Tyco Logistics Engine", layout="wide")

# ================= SECURITY =================
APP_PASSWORD = "tyco2026"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pwd = st.text_input("Access Password", type="password")
    if pwd == APP_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

# ================= DATABASE PATH =================
DATA_DIR = Path.home() / "TycoEngine"
DATA_DIR.mkdir(exist_ok=True)

MASTER_DB = DATA_DIR / "tyco_data.csv"
SEP = ";"

KEY_COLS = ['ShipmntNbr', 'Tracking No', 'Dely No', 'Cust Material Nbr']
QTY_COL = 'Dely Qty'

# ================= FUNCTIONS =================
def load_db():
    if MASTER_DB.exists():
        df = pd.read_csv(MASTER_DB, sep=SEP, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame()

def save_db(df):
    df.to_csv(MASTER_DB, index=False, sep=SEP, encoding="utf-8-sig")

def clean_df(df):
    df.columns = df.columns.str.strip()
    df[QTY_COL] = pd.to_numeric(df.get(QTY_COL, 0), errors="coerce").fillna(0)
    return df

# ================= SIDEBAR =================
with st.sidebar:
    st.header("Data Management")

    db = load_db()
    st.metric("Total History Records", len(db))

    if not db.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            db.to_excel(writer, index=False, sheet_name="Data")
        st.download_button(
            "Download Full History (Data)",
            buffer.getvalue(),
            "Tyco_Full_Data.xlsx"
        )

    st.divider()

    uploaded_file = st.file_uploader(
        "Upload Daily Sheet (Excel)",
        type=["xlsx"],
        key="upload_file"
    )

    if uploaded_file:
        st.warning("Do you want to add this sheet to storage?")

        col1, col2 = st.columns(2)
        confirm = col1.button("Yes, add to storage")
        cancel = col2.button("No, cancel")

        if confirm:
            try:
                new_df = pd.read_excel(uploaded_file, sheet_name="Data")
                new_df = clean_df(new_df)

                valid_keys = [c for c in KEY_COLS if c in new_df.columns]
                new_df = new_df.groupby(valid_keys, as_index=False)[QTY_COL].sum()

                new_df["Load_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                combined = pd.concat([db, new_df], ignore_index=True)
                combined = combined.drop_duplicates(
                    subset=valid_keys,
                    keep="last"
                )

                save_db(combined)

                st.success("Sheet added to storage successfully.")

                st.session_state.upload_file = None
                st.rerun()

            except Exception as e:
                st.error(f"Upload failed: {e}")

        if cancel:
            st.info("Upload cancelled. Nothing was stored.")
            st.session_state.upload_file = None
            st.rerun()

# ================= MAIN =================
st.title("Tyco Logistics Engine")
st.caption("Developed by Eng-Ahmed Hassany")

db = load_db()

if db.empty:
    st.info("Database is empty. Upload a daily sheet (Data sheet only).")
    st.stop()

st.subheader("Auto Search & Results")

# ----------- FILTERS (AUTO) -----------
c1, c2, c3 = st.columns(3)
ship = c1.text_input("Shipment No")
dely = c2.text_input("Delivery No")
mat = c3.text_input("Material Nbr")

track_list = st.text_area(
    "Paste Tracking Numbers (one per line)",
    height=130,
    placeholder="Paste tracking numbers here"
)

filtered = db.copy()

if ship:
    filtered = filtered[filtered['ShipmntNbr'].astype(str).str.contains(ship, case=False, na=False)]

if dely:
    filtered = filtered[filtered['Dely No'].astype(str).str.contains(dely, case=False, na=False)]

if mat:
    filtered = filtered[filtered['Cust Material Nbr'].astype(str).str.contains(mat, case=False, na=False)]

if track_list:
    tracks = [t.strip() for t in track_list.splitlines() if t.strip()]
    filtered = filtered[filtered['Tracking No'].astype(str).isin(tracks)]

# ----------- SUMMARY -----------
summary = (
    filtered
    .groupby(KEY_COLS, as_index=False)[QTY_COL]
    .sum()
)

st.write(f"Results Found: {len(summary)}")
st.dataframe(summary, use_container_width=True)

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    summary.to_excel(writer, index=False, sheet_name="Summary")

st.download_button(
    "Download Result",
    buffer.getvalue(),
    "Tyco_Search_Result.xlsx"
)
