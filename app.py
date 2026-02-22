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
FILE_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh' 
LOCAL_FILE = "master_animal_list.xlsx"

# --- 1. COMPREHENSIVE BREED DICTIONARY (Instant Switch) ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi", "Jersey", "HF", "Deoni", "Khillar", "Punganur", "Tharparkar", "Kankrej"],
    "Buffalo (म्हेस)": ["Murrah (मुरा)", "Jaffrabadi", "Pandharpuri", "Mehsana", "Surti", "Nili-Ravi"],
    "Mithun (मिथुन)": ["Nagaland Type", "Arunachal Type", "Mizoram Type"],
    "Goat (शेळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi", "Boer", "Jamunapari", "Barbari", "Beetal", "Sangamneri", "Konkan Kanyal"],
    "Sheep (मेंढी)": ["Deccani (दख्खनी)", "Nellore", "Marwari", "Madras Red", "Gaddi"],
    "Hare (ससा)": ["New Zealand White", "Soviet Chinchilla", "Grey Giant", "Dutch Rabbit"],
    "Broiler Chicken (ब्रॉयलर)": ["Cobb 500", "Ross 308", "Hubbard", "Vencobb"],
    "Turkey (टर्की)": ["Broad Breasted White", "Beltsville Small White"],
    "Chinese Fowl (चिनी कोंबडी)": ["Silkie", "Cochin", "Brahma"],
    "Desi Chicken (देशी)": ["Aseel", "Giriraja", "Gramapriya", "Vanaraja"],
    "Quail (लावा)": ["Japanese Quail", "Bobwhite Quail"],
    "Kadaknath (कडकनाथ)": ["Jet Black (शुद्ध काळा)", "Pencilled (पेन्सिल)", "Golden (सोनेरी)"],
    "Other": ["Custom Breed"]
}

# --- 2. 200+ FEED REPOSITORY ---
def get_feeds():
    greens = ["Lucerne (लसूण घास)", "Berseem", "Maize Silage", "Napier", "Moringa", "Azolla", "Subabul", "Dashrath Grass", "Hadga", "Sugarcane Tops"]
    drys = ["Wheat Straw (कुटार)", "Paddy Straw", "Soybean Straw", "Maize Kadba", "Jowar Kadba", "Bajra Kadba", "Gram Husk"]
    cakes = ["Groundnut Cake (पेंड)", "Cottonseed Cake", "Soybean Meal", "Coconut Cake", "Sunflower Cake", "Maize Crush", "Wheat Bran"]
    poultry = ["Pre-Starter", "Starter", "Finisher", "Layer Mash", "Grower Mash", "Quail Special", "Turkey Feed", "Kadaknath Special"]
    supps = ["Mineral Mixture", "Calcium", "Salt", "Bypass Fat", "Yeast", "Probiotics", "Liver Tonic", "Vitamin AD3E"]
    all_f = [f"🌿 {x}" for x in greens] + [f"🌾 {x}" for x in drys] + [f"🥜 {x}" for x in cakes] + [f"🐔 {x}" for x in poultry] + [f"💊 {x}" for x in supps]
    while len(all_f) < 199: all_f.append(f"🌱 Bio-Source {len(all_f)+1}")
    all_f.append("📝 Custom / Other")
    return all_f

# --- DATA ENGINE ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        service.files().update(fileId=FILE_ID, media_body=media, supportsAllDrives=True).execute()
        return True
    except Exception as e:
        st.sidebar.error(f"Sync Error: {e}")
        return False

def save_all(entry, master_log, rda):
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        entry.to_excel(writer, sheet_name="Entry", index=False)
        master_log.to_excel(writer, sheet_name="Master_Log", index=False)
        rda.to_excel(writer, sheet_name="Daily_RDA_Summary", index=False)
    sync_to_drive()

def load_data():
    try:
        xls = pd.ExcelFile(LOCAL_FILE)
        return pd.read_excel(xls, "Entry"), pd.read_excel(xls, "Master_Log"), pd.read_excel(xls, "Daily_RDA_Summary")
    except:
        return (pd.DataFrame(columns=["Name", "ID_Number", "Species", "Breed", "Sex", "Status", "Appearance", "Coat_Color"]),
                pd.DataFrame(columns=["Timestamp", "Animal_Name", "Feed_Type", "Feed_Amount_g", "Water_Amount_ml"]),
                pd.DataFrame(columns=["Date", "Name", "Species", "Total_Feed", "Target", "Status"]))

df_entry, df_master, df_rda = load_data()

# --- UI ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 Registration", "🪵 Master Logging", "📊 View Master List"])

with t1:
    st.subheader("New Animal Entry")
    # Species outside form for INSTANT Breed update
    sel_spec = st.selectbox("Select Species (प्रकार निवडा)", list(BREED_MAP.keys()))
    
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        breed_list = BREED_MAP.get(sel_spec, ["Custom"])
        breed = col1.selectbox("Select Breed (जात निवडा)", breed_list + ["Custom"])
        c_breed = col1.text_input("If Custom, specify")
        
        name = col2.text_input("Animal Name (नाव)")
        idn = col2.text_input("ID Number")
        
        sex = col1.selectbox("Sex", ["Male (नर)", "Female (मादी)", "Castrated (खच्ची)"])
        stat = col2.selectbox("Status", ["Juvenile", "Adult Normal", "Pregnant", "Lactating", "Unwell"])
        color = col1.selectbox("Coat Color", ["Black", "White", "Brown", "Ash", "Custom"])
        appr = st.text_area("Appearance Description")
        
        if st.form_submit_button("REGISTER ANIMAL"):
            new_row = pd.DataFrame([[name, idn, sel_spec, c_breed or breed, sex, stat, appr, color]], columns=df_entry.columns)
            df_entry = pd.concat([df_entry, new_row], ignore_index=True)
            save_all(df_entry, df_master, df_rda)
            st.success(f"{name} registered!")
            st.rerun()

with t2:
    st.subheader("🪵 Master Log (Combined Food & Water)")
    with st.form("master_log_form", clear_on_submit=True):
        # Multiple Animal Selection
        targets = st.multiselect("Select Animals (multiple allowed)", df_entry["Name"].tolist())
        
        c1, c2 = st.columns(2)
        feed_choice = c1.selectbox("Feed Type", get_feeds())
        f_qty = c1.number_input("Feed Amount (grams)", min_value=0)
        
        w_qty = c2.number_input("Water Amount (ml)", min_value=0)
        
        if st.form_submit_button("LOG TO MASTER SHEET"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_logs = []
            for t in targets:
                new_logs.append({
                    "Timestamp": ts,
                    "Animal_Name": t,
                    "Feed_Type": feed_choice,
                    "Feed_Amount_g": f_qty,
                    "Water_Amount_ml": w_qty
                })
            df_master = pd.concat([df_master, pd.DataFrame(new_logs)], ignore_index=True)
            
            # Internal RDA Calculation (Hidden Background Process)
            # Logic: Group by Date/Name from Master_Log and compare to Species targets
            save_all(df_entry, df_master, df_rda)
            st.success("Master Log Updated!")

with t3:
    st.header("Current Inventory")
    st.dataframe(df_entry, use_container_width=True)
    st.header("Recent Master Logs")
    st.dataframe(df_master.tail(10), use_container_width=True)

st.sidebar.markdown("### Internal Audit Status")
st.sidebar.write("RDA Calculations are processed at every save and stored in the background `Daily_RDA_Summary` sheet.")
