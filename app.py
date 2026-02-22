import streamlit as st
import pandas as pd
import os
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# --- CONFIGURATION ---
st.set_page_config(page_title="Narayan Farms Bio-Strategist", page_icon="🐾", layout="wide")

# PASTE YOUR FILE ID HERE (From the browser URL)
TARGET_FILE_ID = '1AyehP_JxPkmiE0ii6rebVQC_wzA-2WhwB4sGIcRw3uA' 
LOCAL_FILE = "master_animal_list.xlsx"

# --- 1. BREED & FEED (RETAINED EXACTLY) ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi", "Jersey", "HF", "Deoni", "Khillar", "Punganur", "Tharparkar"],
    "Buffalo (म्हेस)": ["Murrah (मुरा)", "Jaffrabadi", "Pandharpuri", "Mehsana", "Surti", "Nili-Ravi"],
    "Goat (शेळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi", "Boer", "Jamunapari", "Barbari", "Beetal", "Sangamneri"]
}

def get_feeds():
    greens = ["Lucerne (लसूण घास)", "Maize Silage", "Hybrid Napier", "Moringa", "Azolla", "Subabul"]
    drys = ["Wheat Straw (कुटार)", "Paddy Straw", "Soybean Straw", "Maize Kadba", "Jowar Kadba"]
    cakes = ["Groundnut Cake (पेंड)", "Cottonseed Cake", "Soybean Meal", "Maize Crush", "Wheat Bran"]
    supps = ["Mineral Mixture (खनिज मिश्रण)", "Calcium", "Salt", "Bypass Fat", "Yeast", "Probiotics"]
    base_f = [f"🌿 {x}" for x in greens] + [f"🌾 {x}" for x in drys] + [f"🥜 {x}" for x in cakes] + [f"💊 {x}" for x in supps]
    while len(base_f) < 199: base_f.append(f"📦 Farm Resource {len(base_f)+1}")
    base_f.append("📝 Custom / Other (मजकूर लिहा)")
    return base_f

# --- 2. THE DIRECT-LINK SYNC ENGINE ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build('drive', 'v3', credentials=creds)
        
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # We NO LONGER 'create'. We only 'update' the file ID YOU own.
        # This forces Google to use YOUR storage quota.
        service.files().update(
            fileId=TARGET_FILE_ID, 
            media_body=media, 
            supportsAllDrives=True
        ).execute()
        
        st.sidebar.success("✅ Master Excel Updated Successfully!")
        return True
    except Exception as e:
        st.sidebar.error(f"Sync Fail: {e}")
        st.sidebar.info("Ensure the Service Account is an 'Editor' on the NEW file.")
        return False

# --- 3. SAVE & LOAD LOGIC (NO CHANGES) ---
def save_all_sheets(entry, master, rda):
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        entry.to_excel(writer, sheet_name="Entry", index=False)
        master.to_excel(writer, sheet_name="Master_Log", index=False)
        rda.to_excel(writer, sheet_name="Daily_RDA_Summary", index=False)
    sync_to_drive()

def load_data():
    if os.path.exists(LOCAL_FILE):
        try:
            xls = pd.ExcelFile(LOCAL_FILE)
            return (pd.read_excel(xls, "Entry"), pd.read_excel(xls, "Master_Log"), pd.read_excel(xls, "Daily_RDA_Summary"))
        except: pass
    return (pd.DataFrame(columns=["Name", "ID_Number", "Species", "Breed", "Sex", "Status", "Appearance", "Coat_Color"]),
            pd.DataFrame(columns=["Timestamp", "Animal_Name", "Feed_Type", "Feed_Amount_g", "Water_Amount_ml"]),
            pd.DataFrame(columns=["Date", "Name", "Species", "Total_Feed", "Target", "Status"]))

df_entry, df_master, df_rda = load_data()

# --- 4. UI INTERFACE (NO CHANGES) ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 Registration", "🪵 Master Log", "📊 Master List"])

with t1:
    sel_spec = st.selectbox("Select Species (प्रकार निवडा)", list(BREED_MAP.keys()))
    with st.form("reg"):
        c1, c2 = st.columns(2)
        breed = c1.selectbox("Select Breed", BREED_MAP.get(sel_spec, []) + ["Custom"])
        name = c2.text_input("Name")
        idn = c1.text_input("ID")
        sex = c2.selectbox("Sex", ["Male", "Female", "Castrated"])
        stat = c1.selectbox("Status", ["Juvenile", "Adult", "Pregnant", "Lactating", "Unwell"])
        color = c2.selectbox("Color", ["Black", "White", "Brown", "Ash", "Other"])
        appr = st.text_area("Notes")
        if st.form_submit_button("REGISTER"):
            new_row = pd.DataFrame([[name, idn, sel_spec, breed, sex, stat, appr, color]], columns=df_entry.columns)
            df_entry = pd.concat([df_entry, new_row], ignore_index=True)
            save_all_sheets(df_entry, df_master, df_rda)
            st.rerun()

with t2:
    if not df_entry.empty:
        with st.form("log"):
            targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
            c1, c2 = st.columns(2)
            feed = c1.selectbox("Feed Type", get_feeds())
            f_qty = c1.number_input("Feed (g)", min_value=0)
            w_qty = c2.number_input("Water (ml)", min_value=0)
            if st.form_submit_button("LOG TO MASTER SHEET"):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_logs = pd.DataFrame([{"Timestamp": ts, "Animal_Name": t, "Feed_Type": feed, "Feed_Amount_g": f_qty, "Water_Amount_ml": w_qty} for t in targets])
                df_master = pd.concat([df_master, new_logs], ignore_index=True)
                save_all_sheets(df_entry, df_master, df_rda)
                st.success("Master Log Updated!")
    else:
        st.warning("Register animals first.")

with t3:
    st.dataframe(df_entry, use_container_width=True)
    st.dataframe(df_master.tail(15), use_container_width=True)
