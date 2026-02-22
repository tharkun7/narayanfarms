import streamlit as st
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

st.set_page_config(page_title="Narayan Farms Bio-Strategist", page_icon="🐾", layout="wide")

# --- CONFIGURATION ---
FILE_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh' 
LOCAL_FILE = "master_animal_list.xlsx"

# --- EXHAUSTIVE BREED DICTIONARY (Strict Filtering) ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi", "Jersey", "HF", "Deoni", "Khillar", "Tharparkar"],
    "Buffalo (म्हेस)": ["Murrah (मुरा)", "Jaffrabadi", "Pandharpuri", "Mehsana", "Surti"],
    "Mithun (मिथुन)": ["Nagaland Type", "Arunachal Type", "Mizoram Type"],
    "Goat (शेळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi", "Boer", "Jamunapari", "Barbari", "Beetal", "Sangamneri"],
    "Sheep (मेंढी)": ["Deccani", "Nellore", "Marwari", "Madras Red"],
    "Hare (ससा)": ["New Zealand White", "Soviet Chinchilla", "Grey Giant"],
    "Broiler Chicken (ब्रॉयलर)": ["Cobb 500", "Ross 308", "Vencobb"],
    "Turkey (टर्की)": ["Broad Breasted White", "Beltsville Small White"],
    "Chinese Fowl (चिनी कोंबडी)": ["Silkie", "Cochin", "Brahma"],
    "Desi Chicken (देशी)": ["Aseel", "Giriraja", "Gramapriya"],
    "Quail (लावा)": ["Japanese Quail", "Bobwhite Quail"],
    "Kadaknath (कडकनाथ)": ["Jet Black", "Pencilled", "Golden"],
    "Other": ["Custom Breed"]
}

# --- SPECIES RDA TARGETS (Grams per Day) ---
RDA_TARGETS = {
    "Cow (गाय)": 8000, "Buffalo (म्हेस)": 9000, "Mithun (मिथुन)": 7000,
    "Goat (शेळी)": 1500, "Sheep (मेंढी)": 1500, "Hare (ससा)": 150,
    "Broiler Chicken (ब्रॉयलर)": 120, "Turkey (टर्की)": 250, 
    "Chinese Fowl (चिनी कोंबडी)": 100, "Desi Chicken (देशी)": 100,
    "Quail (लावा)": 30, "Kadaknath (कडकnath)": 100, "Other": 500
}

# --- DATA OPERATIONS ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        service.files().update(fileId=FILE_ID, media_body=media, supportsAllDrives=True).execute()
        st.sidebar.success("✅ Cloud Synced")
    except Exception as e:
        st.sidebar.error(f"Sync Failed: {e}")

def save_all(entry, logs, rda):
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        entry.to_excel(writer, sheet_name="Entry", index=False)
        logs.to_excel(writer, sheet_name="Log_History", index=False)
        rda.to_excel(writer, sheet_name="Daily_RDA_Summary", index=False)
    sync_to_drive()

def load_data():
    try:
        xls = pd.ExcelFile(LOCAL_FILE)
        e = pd.read_excel(xls, "Entry")
        l = pd.read_excel(xls, "Log_History")
        r = pd.read_excel(xls, "Daily_RDA_Summary")
        return e, l, r
    except:
        return (pd.DataFrame(columns=["Name", "ID_Number", "Species", "Breed", "Sex", "Status", "Appearance", "Coat_Color"]),
                pd.DataFrame(columns=["Timestamp", "Name", "Type", "Category", "Qty"]),
                pd.DataFrame(columns=["Date", "Name", "Species", "Total_Qty", "Target", "RDA_Satisfied"]))

df_entry, df_logs, df_rda = load_data()

# --- UI TABS ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 New Entry", "🍴 Logging", "📊 Daily RDA Summary"])

with t1:
    with st.form("reg"):
        col1, col2 = st.columns(2)
        name = col1.text_input("Animal Name (नाव)")
        idn = col2.text_input("ID Number")
        spec = col1.selectbox("Species (प्रकार)", list(BREED_MAP.keys()))
        # STRICT BREED FILTERING
        breed = col2.selectbox("Breed (जात)", BREED_MAP[spec] + ["Custom"])
        c_breed = col2.text_input("Enter Breed if Custom") if breed == "Custom" else ""
        
        sex = col1.selectbox("Sex", ["Male", "Female", "Castrated"])
        stat = col2.selectbox("Status", ["Juvenile", "Adult Normal", "Pregnant", "Lactating", "Unwell"])
        color = col1.selectbox("Coat Color", ["Black", "White", "Brown", "Ash", "Other"])
        appr = col2.text_area("Appearance (Optional)")
        
        if st.form_submit_button("REGISTER"):
            new_row = pd.DataFrame([[name, idn, spec, c_breed or breed, sex, stat, appr, color]], columns=df_entry.columns)
            df_entry = pd.concat([df_entry, new_row], ignore_index=True)
            save_all(df_entry, df_logs, df_rda)
            st.rerun()

with t2:
    st.subheader("Food & Water History Logs")
    with st.form("log_form"):
        targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
        mode = st.radio("Log Type", ["Food (चारा)", "Water (पाणी)"], horizontal=True)
        qty = st.number_input("Quantity (g or ml)", min_value=1)
        if st.form_submit_button("SAVE LOGS"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_logs = pd.DataFrame([{"Timestamp": ts, "Name": t, "Type": mode, "Category": "Manual", "Qty": qty} for t in targets])
            df_logs = pd.concat([df_logs, new_logs], ignore_index=True)
            save_all(df_entry, df_logs, df_rda)
            st.success("History Updated")

with t3:
    st.subheader("Daily Nutrient Satisfaction Indicator")
    # Calculation for "Yesterday" (The Midnight Logic)
    target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    st.write(f"Showing Analysis for: {target_date}")
    
    if not df_logs.empty:
        # Filter food logs for the date
        df_logs['Date'] = df_logs['Timestamp'].str[:10]
        day_data = df_logs[(df_logs['Date'] == target_date) & (df_logs['Type'].str.contains("Food"))]
        
        summary = day_data.groupby('Name')['Qty'].sum().reset_index()
        summary = summary.merge(df_entry[['Name', 'Species']], on='Name', how='left')
        
        def calculate_rda(row):
            target = RDA_TARGETS.get(row['Species'], 500)
            satisfied = row['Qty'] >= target
            return pd.Series([target, "✅ Met" if satisfied else "❌ Failed"])

        if not summary.empty:
            summary[['Target', 'Status']] = summary.apply(calculate_rda, axis=1)
            
            # CSS for Red Boundary on Failed RDA
            def highlight_failed(s):
                return ['background-color: #ffcccc; border: 2px solid red' if v == "❌ Failed" else '' for v in s]
            
            st.dataframe(summary.style.apply(highlight_failed, subset=['Status']), use_container_width=True)
            
            if st.button("Archive to Excel RDA Sheet"):
                summary['Date'] = target_date
                df_rda = pd.concat([df_rda, summary], ignore_index=True)
                save_all(df_entry, df_logs, df_rda)
        else:
            st.warning("No data found for the previous day.")

st.sidebar.markdown("---")
st.sidebar.write("Quick View: Total Animals", len(df_entry))
st.sidebar.dataframe(df_entry[["Name", "Species"]])
