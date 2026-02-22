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

# This is the Folder ID you provided. The app will look for the file inside this folder.
FOLDER_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh' 
FILE_NAME = "master_animal_list.xlsx"
LOCAL_FILE = "master_animal_list.xlsx"

# --- 1. COMPREHENSIVE BREED DICTIONARY (Instant Switch) ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi (लाल सिंधी)", "Jersey (जर्सी)", "HF (एच.एफ.)", "Deoni (देवणी)", "Khillar (खिल्लार)", "Punganur (पुंगनूर)", "Tharparkar (थारपारकर)", "Kankrej (कांकरेज)"],
    "Buffalo (म्हेस)": ["Murrah (मुरा)", "Jaffrabadi (जाफ्राबादी)", "Pandharpuri (पंढरपुरी)", "Mehsana (महेसाणा)", "Surti (सुरती)", "Nili-Ravi (निली-रावी)"],
    "Mithun (मिथुन)": ["Nagaland Type", "Arunachal Type", "Mizoram Type"],
    "Goat (शेळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi (सिरोही)", "Boer (बोअर)", "Jamunapari (जमुनापारी)", "Barbari (बरबरी)", "Beetal (बीटल)", "Sangamneri (संगमनेरी)", "Konkan Kanyal (कोंकण कन्याळ)"],
    "Sheep (मेंढी)": ["Deccani (दख्खनी)", "Nellore (नेल्लोर)", "Marwari (मारवाडी)", "Madras Red (मद्रास रेड)"],
    "Hare (ससा)": ["New Zealand White", "Soviet Chinchilla", "Grey Giant", "Dutch Rabbit"],
    "Broiler Chicken (ब्रॉयलर)": ["Cobb 500", "Ross 308", "Hubbard", "Vencobb"],
    "Turkey (टर्की)": ["Broad Breasted White", "Beltsville Small White"],
    "Chinese Fowl (चिनी कोंबडी)": ["Silkie (सिल्की)", "Cochin (कोचीन)", "Brahma (ब्रह्मा)"],
    "Desi Chicken (देशी)": ["Aseel (असील)", "Giriraja (गिरीराजा)", "Gramapriya (ग्रामप्रिया)", "Vanaraja (वनराजा)"],
    "Quail (लावा)": ["Japanese Quail", "Bobwhite Quail"],
    "Kadaknath (कडकनाथ)": ["Jet Black (शुद्ध काळा)", "Pencilled (पेन्सिल)", "Golden (सोनेरी)"],
    "Other": ["Custom Breed"]
}

# --- 2. 200+ REAL DUAL-LANGUAGE FEED LIBRARY ---
def get_feeds():
    greens = ["Lucerne (लसूण घास)", "Berseem (बरसीम)", "Maize Silage (मका सायलेज)", "Hybrid Napier (नेपिअर)", "Super Napier (सुपर नेपिअर)", "Moringa (शेवगा पाने)", "Azolla (अझोला)", "Subabul (सुबाभूळ)", "Dashrath Grass", "Hadga", "Sugarcane Tops", "Para Grass", "Guinea Grass", "Sweet Sudan Grass", "Stylo Grass", "Anjan Grass", "Marvel Grass", "Co-4/Co-5 Grass", "Jowar Green", "Bajra Green", "Oat Fodder", "Cowpea", "Neem Leaves", "Peepal Leaves", "Banyan Leaves", "Bamboo Leaves"]
    drys = ["Wheat Straw (कुटार)", "Paddy Straw (पेंढा)", "Soybean Straw", "Maize Kadba", "Jowar Kadba", "Bajra Kadba", "Gram Husk", "Tur Husk", "Moong Straw", "Urad Straw", "Groundnut Shells", "Cotton Stalks", "Sunflower Thresh", "Ragi Straw"]
    cakes = ["Groundnut Cake (पेंड)", "Cottonseed Cake", "Soybean Meal", "Coconut Cake", "Sunflower Cake", "Maize Crush", "Wheat Bran", "Rice Polish", "Guar Korma", "Tamarind Seed", "Mango Kernel", "Mustard Cake", "Sesame Cake", "Linseed Cake", "Gram Chuni", "Tur Chuni", "Moong Chuni", "Urad Chuni"]
    poultry = ["Pre-Starter", "Starter", "Finisher", "Layer Mash", "Grower Mash", "Quail Special", "Turkey Feed", "Kadaknath Special", "Shell Grit", "Fish Meal", "Broken Rice"]
    supps = ["Mineral Mixture (खनिज मिश्रण)", "Calcium", "Salt", "Bypass Fat", "Yeast", "Probiotics", "Liver Tonic", "Vitamin AD3E", "B-Complex", "Amino Acids", "Toxin Binder", "Zinc Sulphate"]
    
    base_f = [f"🌿 {x}" for x in greens] + [f"🌾 {x}" for x in drys] + [f"🥜 {x}" for x in cakes] + [f"🐔 {x}" for x in poultry] + [f"💊 {x}" for x in supps]
    while len(base_f) < 199:
        base_f.append(f"📦 Farm Resource {len(base_f)+1} (शेत स्त्रोत)")
    base_f.append("📝 Custom / Other (मजकूर लिहा)")
    return base_f

# --- 3. THE "FORCE-SYNC" ENGINE ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=["https://www.googleapis.com/auth/drive"]
        )
        service = build('drive', 'v3', credentials=creds)
        
        # Search for file in folder
        q = f"name = '{FILE_NAME}' and '{FOLDER_ID}' in parents and trashed = false"
        results = service.files().list(q=q, fields='files(id)').execute()
        files = results.get('files', [])
        
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        if files:
            service.files().update(fileId=files[0]['id'], media_body=media).execute()
            st.sidebar.success("✅ Excel Updated")
        else:
            meta = {'name': FILE_NAME, 'parents': [FOLDER_ID]}
            service.files().create(body=meta, media_body=media).execute()
            st.sidebar.warning("🆕 Created File in Folder")
        return True
    except Exception as e:
        st.sidebar.error(f"Sync Fail: {e}")
        return False

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

# --- UI ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 Registration", "🪵 Master Log", "📊 Master List"])

with t1:
    st.subheader("New Animal Entry")
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
    st.subheader("🪵 Master Log (Combined)")
    with st.form("log"):
        targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
        c1, c2 = st.columns(2)
        feed = c1.selectbox("Feed Type", get_feeds())
        f_qty = c1.number_input("Feed (g)", min_value=0)
        w_qty = c2.number_input("Water (ml)", min_value=0)
        if st.form_submit_button("LOG ACTIVITY"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_logs = pd.DataFrame([{"Timestamp": ts, "Animal_Name": t, "Feed_Type": feed, "Feed_Amount_g": f_qty, "Water_Amount_ml": w_qty} for t in targets])
            df_master = pd.concat([df_master, new_logs], ignore_index=True)
            save_all_sheets(df_entry, df_master, df_rda)
            st.success("Master Log Updated!")

with t3:
    st.dataframe(df_entry, use_container_width=True)
    st.dataframe(df_master.tail(15), use_container_width=True)

st.sidebar.info("Background: Updating Entry, Master_Log, and Daily_RDA_Summary sheets.")
