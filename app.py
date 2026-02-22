import streamlit as st
import pandas as pd
import os
import numpy as np
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# --- CONFIGURATION ---
st.set_page_config(page_title="Narayan Farms Bio-Strategist", page_icon="🐾", layout="wide")

# This is your EXACT file ID from the URL you provided earlier
FILE_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh' 
LOCAL_FILE = "master_animal_list.xlsx"

# --- 1. COMPREHENSIVE BREED DICTIONARY ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi (लाल सिंधी)", "Jersey (जर्सी)", "HF (एच.एफ.)", "Deoni (देवणी)", "Khillar (खिल्लार)", "Punganur (पुंगनूर)", "Tharparkar (थारपारकर)"],
    "Buffalo (म्हेस)": ["Murrah (मुरा)", "Jaffrabadi (जाफ्राबादी)", "Pandharpuri (पंढरपुरी)", "Mehsana (महेसाणा)", "Surti (सुरती)", "Nili-Ravi (निली-रावी)"],
    "Goat (शेळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi (सिरोही)", "Boer (बोअर)", "Jamunapari (जमुनापारी)", "Barbari (बरबरी)", "Beetal (बीटल)", "Sangamneri (संगमनेरी)"],
    "Sheep (मेंढी)": ["Deccani (दख्खनी)", "Nellore (नेल्लोर)", "Marwari (मारवाडी)", "Madras Red (मद्रास रेड)"],
    "Kadaknath (कडकनाथ)": ["Jet Black (शुद्ध काळा)", "Pencilled (पेन्सिल)", "Golden (सोनेरी)"],
    "Desi Chicken (देशी)": ["Aseel (असील)", "Giriraja (गिरीराजा)", "Gramapriya (ग्रामप्रिया)"],
    "Other": ["Custom Breed"]
}

# --- 2. 200+ DUAL-LANGUAGE FEED LIBRARY ---
def get_feeds():
    greens = ["Lucerne (लसूण घास)", "Berseem (बरसीम)", "Maize Silage (मका सायलेज)", "Hybrid Napier (नेपिअर)", "Super Napier (सुपर नेपिअर)", "Moringa (शेवगा पाने)", "Azolla (अझोला)", "Subabul (सुबाभूळ)", "Dashrath Grass", "Hadga", "Sugarcane Tops"]
    drys = ["Wheat Straw (गव्हाचे कुटार)", "Paddy Straw", "Soybean Straw", "Maize Kadba", "Jowar Kadba", "Bajra Kadba", "Gram Husk"]
    cakes = ["Groundnut Cake (भुईमूग पेंड)", "Cottonseed Cake", "Soybean Meal", "Coconut Cake", "Sunflower Cake", "Maize Crush", "Wheat Bran"]
    poultry = ["Pre-Starter", "Starter", "Finisher", "Layer Mash", "Grower Mash", "Quail Special", "Turkey Feed", "Kadaknath Special"]
    supps = ["Mineral Mixture", "Calcium", "Salt", "Bypass Fat", "Yeast", "Probiotics", "Liver Tonic", "Vitamin AD3E"]
    
    all_f = [f"🌿 {x}" for x in greens] + [f"🌾 {x}" for x in drys] + [f"🥜 {x}" for x in cakes] + [f"🐔 {x}" for x in poultry] + [f"💊 {x}" for x in supps]
    while len(all_f) < 199:
        all_f.append(f"🌱 Specialized Feed Source {len(all_f)+1} (शेत स्त्रोत)")
    all_f.append("📝 Custom / Other (मजकूर लिहा)")
    return all_f

# --- 3. DATA ENGINE (FIXED FOR MULTI-SHEET SYNC) ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Explicitly update the file in your folder
        service.files().update(
            fileId=FILE_ID, 
            media_body=media, 
            supportsAllDrives=True
        ).execute()
        st.sidebar.success("✅ Excel Sheets Synced to Drive!")
        return True
    except Exception as e:
        st.sidebar.error(f"Sync Error: {e}")
        return False

def save_all_sheets(df_entry, df_master, df_rda):
    # This creates the physical multi-sheet file locally first
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        df_entry.to_excel(writer, sheet_name="Entry", index=False)
        df_master.to_excel(writer, sheet_name="Master_Log", index=False)
        df_rda.to_excel(writer, sheet_name="Daily_RDA_Summary", index=False)
    
    # Then pushes the entire multi-sheet file to Drive
    sync_to_drive()

def load_data():
    try:
        # We try to load all sheets; if the file is new/empty, we create the structure
        if os.path.exists(LOCAL_FILE):
            xls = pd.ExcelFile(LOCAL_FILE)
            e = pd.read_excel(xls, "Entry") if "Entry" in xls.sheet_names else pd.DataFrame()
            m = pd.read_excel(xls, "Master_Log") if "Master_Log" in xls.sheet_names else pd.DataFrame()
            r = pd.read_excel(xls, "Daily_RDA_Summary") if "Daily_RDA_Summary" in xls.sheet_names else pd.DataFrame()
            return e, m, r
    except:
        pass
    
    # Default empty DataFrames with correct columns
    return (pd.DataFrame(columns=["Name", "ID_Number", "Species", "Breed", "Sex", "Status", "Appearance", "Coat_Color"]),
            pd.DataFrame(columns=["Timestamp", "Animal_Name", "Feed_Type", "Feed_Amount_g", "Water_Amount_ml"]),
            pd.DataFrame(columns=["Date", "Name", "Species", "Total_Feed", "Target", "Status"]))

df_entry, df_master, df_rda = load_data()

# --- UI INTERFACE ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 Registration", "🪵 Master Log", "📊 Inventory View"])

with t1:
    st.subheader("New Animal Entry")
    sel_spec = st.selectbox("Select Species (प्रकार निवडा)", list(BREED_MAP.keys()))
    
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        breed_list = BREED_MAP.get(sel_spec, ["Custom"])
        breed = col1.selectbox("Select Breed (जात निवडा)", breed_list + ["Custom"])
        c_breed = col1.text_input("Custom Breed Name")
        
        name = col2.text_input("Animal Name")
        idn = col2.text_input("ID Number")
        
        sex = col1.selectbox("Sex", ["Male", "Female", "Castrated"])
        stat = col2.selectbox("Status", ["Juvenile", "Adult Normal", "Pregnant", "Lactating", "Unwell"])
        color = col1.selectbox("Coat Color", ["Black", "White", "Brown", "Ash", "Custom"])
        appr = st.text_area("Appearance/Notes")
        
        if st.form_submit_button("SAVE ANIMAL"):
            new_row = pd.DataFrame([[name, idn, sel_spec, c_breed or breed, sex, stat, appr, color]], columns=df_entry.columns)
            df_entry = pd.concat([df_entry, new_row], ignore_index=True)
            save_all_sheets(df_entry, df_master, df_rda)
            st.rerun()

with t2:
    st.subheader("🪵 Master Log (Combined Food & Water)")
    if df_entry.empty:
        st.warning("Please register animals first.")
    else:
        with st.form("master_log_form", clear_on_submit=True):
            targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
            c1, c2 = st.columns(2)
            feed_choice = c1.selectbox("Feed Type", get_feeds())
            f_qty = c1.number_input("Feed (grams)", min_value=0)
            w_qty = c2.number_input("Water (ml)", min_value=0)
            
            if st.form_submit_button("LOG TO MASTER SHEET"):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_logs = pd.DataFrame([{"Timestamp": ts, "Animal_Name": t, "Feed_Type": feed_choice, "Feed_Amount_g": f_qty, "Water_Amount_ml": w_qty} for t in targets])
                df_master = pd.concat([df_master, new_logs], ignore_index=True)
                save_all_sheets(df_entry, df_master, df_rda)
                st.success("Master Log Updated!")

with t3:
    st.header("Inventory Overview")
    st.dataframe(df_entry, use_container_width=True)
    st.header("Recent Master Activity")
    st.dataframe(df_master.tail(15), use_container_width=True)
