"""
Tyco Logistics Engine
---------------------
Developed by: Eng-Ahmed Hassany
Classification: Internal Use Only

Rules:
- Storage is based ONLY on sheet named 'Data'
- Duplicate rows inside the same sheet are SUMMED
- Duplicate shipments across days are UPDATED (not duplicated)
"""

import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="Tyco Logistics Engine", layout="wide")

MASTER_DB = "tyco_data.csv"
SEP = ";"

KEY_COLS = ['ShipmntNbr', 'Tracking No', 'Dely No', 'Cust Material Nbr']
QTY_COL = 'Dely Qty'

# ================= FUNCTIONS =================
def load_db():
    if os.path.exists(MASTER_DB):
        df = pd.read_csv(MASTER_DB, sep=SEP, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    return pd.DataFrame()

def save_db(df):
    df.to_csv(MASTER_DB, index=False, sep=SEP, encoding="utf-8-sig")

def clean_df(df):
    df.columns = df.columns.str.strip()
    if QTY_COL in df.columns:
        df[QTY_COL] = pd.to_numeric(df[QTY_COL], errors="coerce").fillna(0)
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
        type=["xlsx"]
    )

    if uploaded_file and st.button("Store Data Sheet"):
        try:
            # Read Data sheet only
            new_df = pd.read_excel(uploaded_file, sheet_name="Data")
            new_df = clean_df(new_df)

            # Aggregate inside the same sheet
            valid_keys = [c for c in KEY_COLS if c in new_df.columns]
            new_df = new_df.groupby(valid_keys, as_index=False)[QTY_COL].sum()

            # Add load timestamp
            new_df["Load_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Merge with database (update logic)
            combined = pd.concat([db, new_df], ignore_index=True)
            combined = combined.drop_duplicates(
                subset=valid_keys,
                keep="last"
            )

            save_db(combined)
            st.success("Data stored successfully.")
            st.rerun()

        except Exception as e:
            st.error(f"Upload failed: {e}")

    if st.checkbox("Advanced: Clear Database"):
        if st.button("Wipe All Data"):
            if os.path.exists(MASTER_DB):
                os.remove(MASTER_DB)
                st.warning("Database cleared.")
                st.rerun()

# ================= MAIN =================
st.title("Tyco Logistics Engine")
st.caption("Developed by Eng-Ahmed Hassany")

db = load_db()

if db.empty:
    st.info("Database is empty. Upload a daily sheet (Data sheet only).")
    st.stop()

st.subheader("Search & Results")

c1, c2, c3, c4 = st.columns(4)
ship = c1.text_input("Shipment No")
track = c2.text_input("Tracking No")
mat = c3.text_input("Material Nbr")
dely = c4.text_input("Delivery No")

filtered = db.copy()

filters = {
    "ShipmntNbr": ship,
    "Tracking No": track,
    "Cust Material Nbr": mat,
    "Dely No": dely
}

for col, val in filters.items():
    if val and col in filtered.columns:
        filtered = filtered[
            filtered[col].astype(str).str.contains(val, case=False, na=False)
        ]

# Summary for display only
group_cols = [c for c in KEY_COLS if c in filtered.columns]

if not filtered.empty and group_cols:
    summary = (
        filtered
        .groupby(group_cols, as_index=False)[QTY_COL]
        .sum()
    )

    st.write(f"Results Found: {len(summary)}")
    st.dataframe(summary, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        summary.to_excel(writer, index=False, sheet_name="Summary")

    st.download_button(
        "Download Search Result",
        buffer.getvalue(),
        "Tyco_Search_Result.xlsx"
    )
else:
    st.info("No results found.")
