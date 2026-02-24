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

TARGET_FILE_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh' 
LOCAL_FILE = "master_animal_list.xlsx"

# --- 1. FULL SPECIES & BREED DICTIONARY ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi", "Jersey", "HF", "Deoni", "Khillar", "Punganur", "Tharparkar", "Kankrej"],
    "Buffalo (म्हेस)": ["Murrah (मुरा)", "Jaffrabadi", "Pandharpuri", "Mehsana", "Surti", "Nili-Ravi"],
    "Mithun (मिथुन)": ["Nagaland Type", "Arunachal Type", "Mizoram Type"],
    "Goat (शेळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi", "Boer", "Jamunapari", "Barbari", "Beetal", "Sangamneri", "Konkan Kanyal"],
    "Sheep (मेंढी)": ["Deccani (दख्खनी)", "Nellore", "Marwari", "Madras Red"],
    "Hare/Rabbit (ससा)": ["New Zealand White", "Soviet Chinchilla", "Grey Giant", "Dutch Rabbit"],
    "Broiler Chicken (ब्रॉयलर)": ["Cobb 500", "Ross 308", "Vencobb"],
    "Turkey (टर्की)": ["Broad Breasted White", "Beltsville Small White"],
    "Chinese Fowl (चिनी कोंबडी)": ["Silkie (सिल्की)", "Cochin", "Brahma"],
    "Desi Chicken (देशी)": ["Aseel (असील)", "Giriraja", "Gramapriya", "Vanaraja"],
    "Quail (लावा)": ["Japanese Quail", "Bobwhite Quail"],
    "Kadaknath (कडकनाथ)": ["Jet Black", "Pencilled", "Golden"],
    "Horse (घोडा)": ["Marwari", "Kathiawari", "Sindhi"],
    "Pig (डुक्कर)": ["Large White Yorkshire", "Landrace"],
    "Other": ["Custom Breed"]
}

# --- 2. FEED & SYNC ENGINE (RETAINED) ---
def get_feeds():
    greens = ["Lucerne (लसूण घास)", "Maize Silage", "Hybrid Napier", "Moringa", "Azolla", "Subabul", "Sugarcane Tops"]
    drys = ["Wheat Straw (कुटार)", "Paddy Straw", "Soybean Straw", "Maize Kadba", "Jowar Kadba"]
    cakes = ["Groundnut Cake (पेंड)", "Cottonseed Cake", "Soybean Meal", "Coconut Cake", "Sunflower Cake"]
    supps = ["Mineral Mixture", "Calcium", "Salt", "Bypass Fat", "Yeast", "Probiotics", "Liver Tonic"]
    base_f = [f"🌿 {x}" for x in greens] + [f"🌾 {x}" for x in drys] + [f"🥜 {x}" for x in cakes] + [f"💊 {x}" for x in supps]
    while len(base_f) < 200: base_f.append(f"📦 Farm Resource {len(base_f)+1}")
    return base_f

def get_service():
    creds_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/drive"])
    return build('drive', 'v3', credentials=creds)

def download_latest():
    try:
        service = get_service()
        request = service.files().get_media(fileId=TARGET_FILE_ID)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        with open(LOCAL_FILE, 'wb') as f: f.write(fh.getvalue())
        return True
    except: return False

def save_all(entry, master, rda):
    nutrition = pd.DataFrame([{"Feed Name": f, "CP%": 12, "TDN%": 60} for f in get_feeds()])
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        entry.to_excel(writer, sheet_name="Entry", index=False)
        master.to_excel(writer, sheet_name="Master_Log", index=False)
        rda.to_excel(writer, sheet_name="Midnight_RDA_Report", index=False)
        nutrition.to_excel(writer, sheet_name="Nutrition_Library", index=False)
    try:
        service = get_service()
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        service.files().update(fileId=TARGET_FILE_ID, media_body=media, supportsAllDrives=True).execute()
        st.sidebar.success("✅ Cloud Data Secure")
    except Exception as e: st.sidebar.error(f"Sync Fail: {e}")

# Initial Boot
if 'booted' not in st.session_state:
    download_latest()
    st.session_state['booted'] = True

try:
    xls = pd.ExcelFile(LOCAL_FILE)
    df_entry = pd.read_excel(xls, "Entry")
    df_master = pd.read_excel(xls, "Master_Log")
    df_rda = pd.read_excel(xls, "Midnight_RDA_Report")
except:
    df_entry = pd.DataFrame(columns=["Name", "ID_Number", "Species", "Breed", "Sex", "Status", "Appearance", "Coat_Color"])
    df_master = pd.DataFrame(columns=["Timestamp", "Animal_Name", "Feed_Type", "Feed_Amount_g", "Water_Amount_ml"])
    df_rda = pd.DataFrame(columns=["Date", "Name", "Total_Feed_g", "Target", "Status"])

# --- 3. UI INTERFACE ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 Bulk Registration", "🪵 Master Log", "📊 Performance & RDA"])

with t1:
    st.subheader("Bulk Animal Registration (घाऊक नोंदणी)")
    sel_spec = st.selectbox("Select Species", list(BREED_MAP.keys()))
    
    with st.form("bulk_reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        breed = col1.selectbox("Select Breed", BREED_MAP.get(sel_spec, []) + ["Custom"])
        # MULTI-ADD LOGIC: Enter names separated by commas
        names_input = col2.text_area("Enter Names/IDs (Separate with commas)", help="Example: Cow1, Cow2, Cow3")
        
        sex = col1.selectbox("Sex", ["Male", "Female", "Castrated"])
        stat = col2.selectbox("Status", ["Juvenile", "Adult Normal", "Pregnant", "Lactating", "Unwell"])
        color = col1.selectbox("Coat Color", ["Black", "White", "Brown", "Ash", "Other"])
        appr = st.text_area("Special Note (Notes will apply to all in this batch)")
        
        if st.form_submit_button("ADD ALL TO DATABASE"):
            if names_input:
                # Splitting names and stripping whitespace
                new_names = [n.strip() for n in names_input.split(",") if n.strip()]
                new_entries = []
                for name in new_names:
                    new_entries.append([name, "N/A", sel_spec, breed, sex, stat, appr, color])
                
                batch_df = pd.DataFrame(new_entries, columns=df_entry.columns)
                df_entry = pd.concat([df_entry, batch_df], ignore_index=True)
                save_all(df_entry, df_master, df_rda)
                st.success(f"Added {len(new_names)} animals successfully!")
                st.rerun()

with t2:
    st.subheader("Daily Activity Log (Multi-Select)")
    with st.form("master_log_form"):
        targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
        c1, c2 = st.columns(2)
        feed_choice = c1.selectbox("Select Feed", get_feeds())
        f_qty = c1.number_input("Feed Amount (grams)", min_value=0)
        w_qty = c2.number_input("Water Amount (ml)", min_value=0)
        
        if st.form_submit_button("LOG TO CLOUD"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            today = datetime.now().strftime("%Y-%m-%d")
            new_logs = pd.DataFrame([{"Timestamp": ts, "Animal_Name": t, "Feed_Type": feed_choice, "Feed_Amount_g": f_qty, "Water_Amount_ml": w_qty} for t in targets])
            df_master = pd.concat([df_master, new_logs], ignore_index=True)
            
            # Midnight RDA Color Logic
            for t in targets:
                total_today = df_master[(df_master['Animal_Name'] == t) & (df_master['Timestamp'].str.startswith(today))]['Feed_Amount_g'].sum()
                status = "GREEN" if total_today >= 2000 else "RED"
                rda_entry = pd.DataFrame([[today, t, total_today, 2000, status]], columns=df_rda.columns)
                df_rda = pd.concat([df_rda, rda_entry]).drop_duplicates(subset=['Date', 'Name'], keep='last')
            
            save_all(df_entry, df_master, df_rda)
            st.success("Activity Logged & RDA Updated")

with t3:
    st.subheader("Midnight RDA Monitor (Red/Green)")
    def highlight_rda(s):
        return ['background-color: green' if v == 'GREEN' else 'background-color: red' for v in s]
    
    if not df_rda.empty:
        st.dataframe(df_rda.style.apply(highlight_rda, subset=['Status']), use_container_width=True)
    
    st.subheader("Current Master List (Total Animals)")
    st.dataframe(df_entry, use_container_width=True)
