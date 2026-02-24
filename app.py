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

# Strict Column Definitions
ENTRY_COLS = ["Name", "ID_Number", "Species", "Breed", "Sex", "Status", "Appearance", "Coat_Color"]
LOG_COLS = ["Timestamp", "Animal_Name", "Feed_Type", "Feed_Amount_g", "Water_Amount_ml"]
RDA_COLS = ["Date", "Name", "Total_Feed_g", "Target", "Status"]

# --- 1. SPECIES & BREED DICTIONARY (RESTORED) ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi", "Jersey", "HF", "Deoni", "Khillar", "Punganur", "Tharparkar"],
    "Buffalo (म्हेस)": ["Murrah (मुरा)", "Jaffrabadi", "Pandharpuri", "Mehsana", "Surti", "Nili-Ravi"],
    "Goat (शेळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi", "Boer", "Jamunapari", "Barbari", "Beetal", "Sangamneri"],
    "Sheep (मेंढी)": ["Deccani (दख्खनी)", "Nellore", "Marwari", "Madras Red"],
    "Poultry/Kadaknath": ["Jet Black", "Pencilled", "Golden", "Aseel", "Giriraja", "Broiler"],
    "Other": ["Custom Breed"]
}

# --- 2. 200+ DUAL-LANGUAGE FEED LIBRARY ---
def get_feeds():
    # Explicit Dual-Language Mapping
    feeds = [
        "🌿 Lucerne (लसूण घास)", "🌿 Maize Silage (मका सायलेज)", "🌿 Hybrid Napier (हायब्रीड नेपिअर)", 
        "🌿 Moringa (शेवगा)", "🌿 Azolla (अझोला)", "🌿 Subabul (सुबाभूळ)", "🌿 Sugarcane Tops (ऊस वाढा)",
        "🌾 Wheat Straw (गव्हाचे कुटार)", "🌾 Paddy Straw (भाताचा पेंढा)", "🌾 Soybean Straw (सोयाबीन कुटार)",
        "🌾 Maize Kadba (मका कडबा)", "🌾 Jowar Kadba (ज्वारी कडबा)", "🌾 Gram Husk (हरभरा भुसा)",
        "🥜 Groundnut Cake (भुईमूग पेंड)", "🥜 Cottonseed Cake (सरकी पेंड)", "🥜 Soybean Meal (सोयाबीन पेंड)",
        "🥜 Coconut Cake (खोबरे पेंड)", "🥜 Sunflower Cake (सूर्यफूल पेंड)", "🥜 Maize Crush (मका भरडा)",
        "🥜 Wheat Bran (गव्हाचा कोंडा)", "🥜 Rice Polish (राईस पॉलिश)", "🥜 Gram Chuni (हरभरा चुनी)",
        "💊 Mineral Mixture (खनिज मिश्रण)", "💊 Calcium (कॅल्शियम)", "💊 Salt (मीठ)", 
        "💊 Bypass Fat (बायपास फॅट)", "💊 Yeast (यीस्ट)", "💊 Probiotics (प्रोबायोटिक्स)",
        "💊 Liver Tonic (लिव्हर टॉनिक)", "💊 Vitamin AD3E (जीवनसत्वे)"
    ]
    # Fill up to 200 items with dual language placeholders
    while len(feeds) < 200:
        feeds.append(f"📦 Farm Resource {len(feeds)+1} (शेत स्त्रोत)")
    return feeds

# --- 3. CLOUD ENGINE ---
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
    nutrition = pd.DataFrame([{"Feed Name": f, "CP%": 12} for f in get_feeds()])
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        entry.reindex(columns=ENTRY_COLS).to_excel(writer, sheet_name="Entry", index=False)
        master.reindex(columns=LOG_COLS).to_excel(writer, sheet_name="Master_Log", index=False)
        rda.reindex(columns=RDA_COLS).to_excel(writer, sheet_name="Midnight_RDA_Report", index=False)
        nutrition.to_excel(writer, sheet_name="Nutrition_Library", index=False)
    try:
        service = get_service()
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        service.files().update(fileId=TARGET_FILE_ID, media_body=media, supportsAllDrives=True).execute()
        st.sidebar.success("✅ Master_Log & All Sheets Synced")
    except Exception as e: st.sidebar.error(f"Sync Fail: {e}")

# Initial Boot
if 'booted' not in st.session_state:
    download_latest()
    st.session_state['booted'] = True

try:
    xls = pd.ExcelFile(LOCAL_FILE)
    df_entry = pd.read_excel(xls, "Entry").reindex(columns=ENTRY_COLS)
    df_master = pd.read_excel(xls, "Master_Log").reindex(columns=LOG_COLS)
    df_rda = pd.read_excel(xls, "Midnight_RDA_Report").reindex(columns=RDA_COLS)
except:
    df_entry = pd.DataFrame(columns=ENTRY_COLS)
    df_master = pd.DataFrame(columns=LOG_COLS)
    df_rda = pd.DataFrame(columns=RDA_COLS)

# --- 4. UI INTERFACE ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 Bulk Registration", "🪵 Master Log", "📊 Performance & RDA"])

with t1:
    st.subheader("Bulk Registration (घाऊक नोंदणी)")
    sel_spec = st.selectbox("Select Species", list(BREED_MAP.keys()))
    with st.form("bulk_reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        breed = col1.selectbox("Select Breed", BREED_MAP.get(sel_spec, []) + ["Custom"])
        names_input = col2.text_area("Enter Names (comma separated)", help="e.g. Cow1, Cow2, Cow3")
        sex = col1.selectbox("Sex", ["Male", "Female", "Castrated"])
        stat = col2.selectbox("Status", ["Juvenile", "Adult", "Pregnant", "Lactating", "Unwell"])
        color = col1.selectbox("Coat Color", ["Black", "White", "Brown", "Ash", "Other"])
        appr = st.text_area("Notes / Appearance")
        
        if st.form_submit_button("ADD TO DATABASE"):
            if names_input:
                new_names = [n.strip() for n in names_input.split(",") if n.strip()]
                new_data = [{"Name": n, "ID_Number": "N/A", "Species": sel_spec, "Breed": breed, "Sex": sex, "Status": stat, "Appearance": appr, "Coat_Color": color} for n in new_names]
                df_entry = pd.concat([df_entry, pd.DataFrame(new_data)], ignore_index=True)
                save_all(df_entry, df_master, df_rda)
                st.rerun()

with t2:
    st.subheader("Daily Activity Log (Master_Log)")
    if not df_entry.empty:
        with st.form("log_form"):
            targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
            c1, c2 = st.columns(2)
            feed = c1.selectbox("Select Feed", get_feeds())
            f_qty = c1.number_input("Feed (g)", min_value=0)
            w_qty = c2.number_input("Water (ml)", min_value=0)
            
            if st.form_submit_button("SAVE FEEDING DATA"):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                today = datetime.now().strftime("%Y-%m-%d")
                new_logs = pd.DataFrame([{"Timestamp": ts, "Animal_Name": t, "Feed_Type": feed, "Feed_Amount_g": f_qty, "Water_Amount_ml": w_qty} for t in targets])
                df_master = pd.concat([df_master, new_logs], ignore_index=True)
                
                for t in targets:
                    total = df_master[(df_master['Animal_Name'] == t) & (df_master['Timestamp'].str.startswith(today))]['Feed_Amount_g'].sum()
                    status = "GREEN" if total >= 2000 else "RED"
                    rda_row = pd.DataFrame([{"Date": today, "Name": t, "Total_Feed_g": total, "Target": 2000, "Status": status}])
                    df_rda = pd.concat([df_rda, rda_row]).drop_duplicates(subset=['Date', 'Name'], keep='last')
                
                save_all(df_entry, df_master, df_rda)
                st.success(f"Master_Log Updated for {len(targets)} animals")
                st.rerun()

with t3:
    st.subheader("Midnight RDA Monitor")
    def highlight_rda(s):
        return ['background-color: green' if v == 'GREEN' else 'background-color: red' for v in s]
    if not df_rda.empty:
        st.dataframe(df_rda.style.apply(highlight_rda, subset=['Status']), use_container_width=True)
    
    st.subheader("Full History (Master_Log)")
    st.dataframe(df_master.tail(15), use_container_width=True)
    
    st.subheader("Inventory")
    st.dataframe(df_entry, use_container_width=True)
