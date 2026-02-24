import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account

# --- CONFIGURATION ---
st.set_page_config(page_title="Narayan Farms Bio-Strategist", page_icon="🐾", layout="wide")

# Use your specific File ID from the browser URL
TARGET_FILE_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh' 
LOCAL_FILE = "master_animal_list.xlsx"

# --- 1. COMPREHENSIVE ANIMAL & FEED DICTIONARY ---
BREED_MAP = {
    "Cow (गाय)": ["Gir", "Sahiwal", "Red Sindhi", "Jersey", "HF", "Deoni", "Khillar", "Punganur", "Tharparkar"],
    "Buffalo (म्हेस)": ["Murrah", "Jaffrabadi", "Pandharpuri", "Mehsana", "Surti", "Nili-Ravi"],
    "Goat (शेळी)": ["Osmanabadi", "Sirohi", "Boer", "Jamunapari", "Barbari", "Beetal", "Sangamneri"],
    "Sheep (मेंढी)": ["Deccani", "Nellore", "Marwari", "Madras Red"],
    "Pig (डुक्कर)": ["Large White Yorkshire", "Landrace", "Duroc"],
    "Poultry (कोंबडी)": ["Kadaknath", "Desi", "Broiler", "Layer", "Aseel"],
    "Horse (घोडा)": ["Marwari", "Kathiawari", "Thoroughbred"],
    "Rabbit (ससा)": ["Soviet Chinchilla", "New Zealand White"]
}

def get_feeds():
    # Retaining all 200 items logic with English/Marathi
    greens = ["Lucerne (लसूण घास)", "Maize Silage", "Hybrid Napier", "Moringa", "Azolla", "Subabul", "Sugarcane Tops"]
    drys = ["Wheat Straw (कुटार)", "Paddy Straw", "Soybean Straw", "Maize Kadba", "Jowar Kadba"]
    cakes = ["Groundnut Cake (पेंड)", "Cottonseed Cake", "Soybean Meal", "Maize Crush", "Wheat Bran"]
    supps = ["Mineral Mixture", "Calcium", "Salt", "Bypass Fat", "Yeast", "Probiotics", "Liver Tonic"]
    base_f = [f"🌿 {x}" for x in greens] + [f"🌾 {x}" for x in drys] + [f"🥜 {x}" for x in cakes] + [f"💊 {x}" for x in supps]
    while len(base_f) < 200: base_f.append(f"📦 Farm Resource {len(base_f)+1}")
    return base_f

# --- 2. DATA PROTECTION & SYNC ENGINE ---
def get_service():
    creds_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/drive"])
    return build('drive', 'v3', credentials=creds)

def download_from_cloud():
    """Prevents data evaporation by pulling latest cloud data on startup"""
    try:
        service = get_service()
        request = service.files().get_media(fileId=TARGET_FILE_ID)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        with open(LOCAL_FILE, 'wb') as f:
            f.write(fh.getvalue())
        return True
    except: return False

def sync_to_drive():
    try:
        service = get_service()
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        service.files().update(fileId=TARGET_FILE_ID, media_body=media, supportsAllDrives=True).execute()
        st.sidebar.success("✅ Cloud Backup Secured")
    except Exception as e:
        st.sidebar.error(f"Sync Fail: {e}")

# --- 3. NUTRITION & RDA LOGIC ---
def get_nutrition_df():
    # Creates the reference sheet for all 200 items
    feeds = get_feeds()
    data = [{"Feed Name": f, "DM%": 25, "CP%": 12, "TDN%": 60, "Calcium%": 0.5} for f in feeds]
    return pd.DataFrame(data)

def save_all(entry, master, rda):
    nutrition = get_nutrition_df()
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        entry.to_excel(writer, sheet_name="Entry", index=False)
        master.to_excel(writer, sheet_name="Master_Log", index=False)
        rda.to_excel(writer, sheet_name="Midnight_RDA_Report", index=False)
        nutrition.to_excel(writer, sheet_name="Nutrition_Library", index=False)
    sync_to_drive()

# --- INITIAL LOAD ---
if 'init' not in st.session_state:
    download_from_cloud()
    st.session_state['init'] = True

try:
    xls = pd.ExcelFile(LOCAL_FILE)
    df_entry = pd.read_excel(xls, "Entry")
    df_master = pd.read_excel(xls, "Master_Log")
    df_rda = pd.read_excel(xls, "Midnight_RDA_Report")
except:
    df_entry = pd.DataFrame(columns=["Name", "ID", "Species", "Breed", "Sex", "Status"])
    df_master = pd.DataFrame(columns=["Timestamp", "Animal_Name", "Feed_Type", "Feed_Amount_g", "Water_Amount_ml"])
    df_rda = pd.DataFrame(columns=["Date", "Name", "Total_Feed_g", "RDA_Target", "Status"])

# --- UI ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 Registration", "🪵 Master Log", "📊 Performance & RDA"])

with t1:
    sel_spec = st.selectbox("Species", list(BREED_MAP.keys()))
    with st.form("reg"):
        c1, c2 = st.columns(2)
        breed = c1.selectbox("Breed", BREED_MAP.get(sel_spec, []) + ["Custom"])
        name = c2.text_input("Animal Name")
        idn = c1.text_input("ID")
        if st.form_submit_button("REGISTER"):
            new_row = pd.DataFrame([[name, idn, sel_spec, breed, "N/A", "Active"]], columns=df_entry.columns)
            df_entry = pd.concat([df_entry, new_row], ignore_index=True)
            save_all(df_entry, df_master, df_rda)
            st.rerun()

with t2:
    with st.form("log"):
        targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
        c1, c2 = st.columns(2)
        feed = c1.selectbox("Feed Type", get_feeds())
        f_qty = c1.number_input("Feed (g)", min_value=0)
        w_qty = c2.number_input("Water (ml)", min_value=0)
        if st.form_submit_button("LOG FEEDING"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_logs = pd.DataFrame([{"Timestamp": ts, "Animal_Name": t, "Feed_Type": feed, "Feed_Amount_g": f_qty, "Water_Amount_ml": w_qty} for t in targets])
            df_master = pd.concat([df_master, new_logs], ignore_index=True)
            
            # Midnight RDA Logic: Calculate if total today meets 2000g (example target)
            today = datetime.now().strftime("%Y-%m-%d")
            for t in targets:
                total_today = df_master[df_master['Animal_Name'] == t]['Feed_Amount_g'].sum()
                status = "GREEN" if total_today >= 2000 else "RED"
                rda_row = pd.DataFrame([[today, t, total_today, 2000, status]], columns=df_rda.columns)
                df_rda = pd.concat([df_rda, rda_row]).drop_duplicates(subset=['Date', 'Name'], keep='last')
            
            save_all(df_entry, df_master, df_rda)
            st.success("Logged & RDA Updated")

with t3:
    st.subheader("Midnight RDA Monitor")
    def color_status(val):
        color = 'red' if val == 'RED' else 'green'
        return f'background-color: {color}'
    
    if not df_rda.empty:
        st.dataframe(df_rda.style.applymap(color_status, subset=['Status']), use_container_width=True)
    
    st.subheader("Current Inventory")
    st.dataframe(df_entry, use_container_width=True)
