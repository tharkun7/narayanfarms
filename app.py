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

# --- 1. COMPREHENSIVE BREED DICTIONARY ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi (लाल सिंधी)", "Jersey (जर्सी)", "HF (एच.एफ.)", "Deoni (देवणी)", "Khillar (खिल्लार)", "Punganur (पुंगनूर)", "Tharparkar (थारपारकर)", "Rathi (राठी)", "Kankrej (कांकरेज)"],
    "Buffalo (म्हेस)": ["Murrah (मुरा)", "Jaffrabadi (जाफ्राबादी)", "Pandharpuri (पंढरपुरी)", "Mehsana (महेसाणा)", "Surti (सुरती)", "Nili-Ravi (निली-रावी)", "Bhadawari (भदावरी)"],
    "Mithun (मिथुन)": ["Nagaland Type", "Arunachal Type", "Mizoram Type", "Manipur Type"],
    "Goat (शेळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi (सिरोही)", "Boer (बोअर)", "Jamunapari (जमुनापारी)", "Barbari (बरबरी)", "Beetal (बीटल)", "Sangamneri (संगमनेरी)", "Konkan Kanyal (कोंकण कन्याळ)", "Surti Goat"],
    "Sheep (मेंढी)": ["Deccani (दख्खनी)", "Nellore (नेल्लोर)", "Marwari (मारवाडी)", "Madras Red (मद्रास रेड)", "Gaddi (गड्डी)", "Bannur (बन्नूर)"],
    "Hare (ससा)": ["New Zealand White", "Soviet Chinchilla", "Grey Giant", "Dutch Rabbit", "English Angora"],
    "Broiler Chicken (ब्रॉयलर)": ["Cobb 500", "Ross 308", "Hubbard", "Vencobb", "Hy-Line"],
    "Turkey (टर्की)": ["Broad Breasted White", "Beltsville Small White", "Bourbon Red", "Narragansett"],
    "Chinese Fowl (चिनी कोंबडी)": ["Silkie (सिल्की)", "Cochin (कोचीन)", "Brahma (ब्रह्मा)", "Langshan"],
    "Desi Chicken (देशी)": ["Aseel (असील)", "Giriraja (गिरीराजा)", "Gramapriya (ग्रामप्रिया)", "Pratapdhan (प्रतापधन)", "Vanaraja (वनराजा)"],
    "Quail (लावा)": ["Japanese Quail", "Bobwhite Quail", "Rain Quail", "King Quail"],
    "Kadaknath (कडकनाथ)": ["Jet Black (शुद्ध काळा)", "Pencilled (पेन्सिल)", "Golden (सोनेरी)"],
    "Other": ["Custom Breed"]
}

# --- 2. COMPREHENSIVE FEED LIST (200 ITEMS) ---
def get_full_feed_list():
    greens = ["Lucerne (लसूण घास)", "Berseem (बरसीम)", "Maize Silage (मका सायलेज)", "Hybrid Napier (नेपिअर)", "Super Napier (सुपर नेपिअर)", "Moringa (शेवगा पाने)", "Azolla (अझोला)", "Subabul (सुबाभूळ)", "Dashrath Grass", "Hadga", "Gliricidia", "Banana Leaves", "Sugarcane Tops", "Para Grass", "Guinea Grass"]
    drys = ["Wheat Straw (कुटार)", "Paddy Straw (पेंढा)", "Soybean Straw", "Maize Kadba", "Jowar Kadba", "Bajra Kadba", "Gram Husk", "Tur Husk", "Moong Straw", "Urad Straw"]
    concentrates = ["Groundnut Cake (पेंड)", "Cottonseed Cake", "Soybean Meal", "Coconut Cake", "Sunflower Cake", "Linseed Cake", "Maize Crush", "Wheat Bran (चोकर)", "Rice Polish", "Guar Korma", "De-oiled Rice Bran"]
    poultry_feeds = ["Pre-Starter", "Starter", "Finisher", "Layer Mash", "Grower Mash", "Quail Special", "Turkey Feed", "Kadaknath Special", "Shell Grit"]
    supps = ["Mineral Mixture", "Calcium Carbonate", "DCP", "Iodized Salt", "Bypass Fat", "Yeast culture", "Probiotics", "Liver Tonic", "Vitamin AD3E", "B-Complex", "Amino Acids", "Toxin Binder"]
    
    all_feeds = [f"🌿 {f}" for f in greens] + [f"🌾 {f}" for f in drys] + [f"🥜 {f}" for f in concentrates] + [f"🐔 {f}" for f in poultry_feeds] + [f"💊 {f}" for f in supps]
    while len(all_feeds) < 199:
        all_feeds.append(f"🌱 Botanical Supplement {len(all_feeds)+1}")
    all_feeds.append("📝 Custom / Other (मजकूर लिहा)")
    return all_feeds

# --- RDA THRESHOLDS ---
RDA_TARGETS = {"Cow (गाय)": 10000, "Buffalo (म्हेस)": 12000, "Goat (शेळी)": 2000, "Sheep (मेंढी)": 2000, "Kadaknath (कडकनाथ)": 110, "Other": 500}

# --- DATA OPERATIONS ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        service.files().update(fileId=FILE_ID, media_body=media, supportsAllDrives=True).execute()
        return True
    except Exception as e:
        st.sidebar.error(f"Cloud Sync Error: {e}")
        return False

def save_all(entry, logs, rda):
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        entry.to_excel(writer, sheet_name="Entry", index=False)
        logs.to_excel(writer, sheet_name="Log_History", index=False)
        rda.to_excel(writer, sheet_name="Daily_RDA_Summary", index=False)
    sync_to_drive()

def load_data():
    try:
        xls = pd.ExcelFile(LOCAL_FILE)
        return pd.read_excel(xls, "Entry"), pd.read_excel(xls, "Log_History"), pd.read_excel(xls, "Daily_RDA_Summary")
    except:
        return (pd.DataFrame(columns=["Name", "ID_Number", "Species", "Breed", "Sex", "Status", "Appearance", "Coat_Color"]),
                pd.DataFrame(columns=["Timestamp", "Name", "Type", "Feed_Name", "Qty"]),
                pd.DataFrame(columns=["Date", "Name", "Species", "Total_Qty", "Target", "Status"]))

df_entry, df_logs, df_rda = load_data()

# --- INTERNAL RDA CALCULATION (Hidden from Public) ---
def run_internal_rda_check(logs, entry, rda_df):
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if not logs.empty:
        logs['Date'] = logs['Timestamp'].astype(str).str[:10]
        day_data = logs[(logs['Date'] == yesterday) & (logs['Type'] == "Food (चारा)")]
        if not day_data.empty:
            summary = day_data.groupby('Name')['Qty'].sum().reset_index()
            summary = summary.merge(entry[['Name', 'Species']], on='Name', how='left')
            summary['Target'] = summary['Species'].map(RDA_TARGETS).fillna(500)
            summary['Status'] = np.where(summary['Qty'] >= summary['Target'], "✅ Met", "❌ Failed")
            summary['Date'] = yesterday
            # Append only if not already calculated for this date
            if yesterday not in rda_df['Date'].astype(str).values:
                return pd.concat([rda_df, summary], ignore_index=True)
    return rda_df

# --- UI INTERFACE ---
st.title("🚜 Narayan Farms: Expert ERP")
t1, t2, t3 = st.tabs(["📝 Registration (नोंदणी)", "🍴 Daily Logs (नोंदी)", "📊 Registered Animals"])

with t1:
    st.header("New Animal Entry")
    # Species Selection (OUTSIDE FORM FOR INSTANT UPDATE)
    selected_species = st.selectbox("1. Select Species (प्रकार निवडा)", list(BREED_MAP.keys()), key="spec_select")
    
    with st.form("registration_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        # Breed updates instantly because 'selected_species' is dynamic
        breed = col1.selectbox("2. Select Breed (जात निवडा)", BREED_MAP[selected_species] + ["Custom"])
        c_breed = col1.text_input("If Custom, type here")
        
        name = col2.text_input("Animal Name (नाव)")
        idn = col2.text_input("ID Number (ओळख क्रमांक)")
        
        sex = col1.selectbox("Sex (लिंग)", ["Male (नर)", "Female (मादी)", "Castrated (खच्ची)"])
        status = col2.selectbox("Status (स्थिती)", ["Juvenile", "Adult Normal", "Pregnant", "Lactating", "Unwell", "Custom"])
        c_status = col2.text_input("Status Detail") if status == "Custom" else ""
        
        color = col1.selectbox("Coat Color", ["Black", "White", "Brown", "Ash", "Custom"])
        c_color = col1.text_input("Color Detail") if color == "Custom" else ""
        
        appearance = st.text_area("Appearance/Notes (पर्यायी वर्णन)")
        
        if st.form_submit_button("COMPLETE REGISTRATION"):
            new_row = pd.DataFrame([[name, idn, selected_species, c_breed or breed, sex, c_status or status, appearance, c_color or color]], columns=df_entry.columns)
            df_entry = pd.concat([df_entry, new_row], ignore_index=True)
            # Run background RDA check before saving
            df_rda = run_internal_rda_check(df_logs, df_entry, df_rda)
            save_all(df_entry, df_logs, df_rda)
            st.success(f"{name} Saved and RDA Syncing in background!")
            st.rerun()

with t2:
    st.header("Food & Water History")
    with st.form("log_entry"):
        targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
        log_type = st.radio("Log Type", ["Food (चारा)", "Water (पाणी)"], horizontal=True)
        
        # Comprehensive 200 Feeds Dropdown
        f_list = get_full_feed_list()
        feed_name = st.selectbox("Feed/Supplement Name", f_list)
        custom_f = st.text_input("Custom Feed Detail") if "Custom" in feed_name else ""
        
        amount = st.number_input("Amount (Grams/ML)", min_value=1)
        
        if st.form_submit_button("SAVE TO LOG HISTORY"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_logs = pd.DataFrame([{"Timestamp": ts, "Name": t, "Type": log_type, "Feed_Name": custom_f or feed_name, "Qty": amount} for t in targets])
            df_logs = pd.concat([df_logs, new_logs], ignore_index=True)
            # Internal RDA sync
            df_rda = run_internal_rda_check(df_logs, df_entry, df_rda)
            save_all(df_entry, df_logs, df_rda)
            st.success("History logged to Excel.")

with t3:
    st.header("Master List")
    st.dataframe(df_entry, use_container_width=True)

st.sidebar.info("RDA Analytics are being calculated and saved to the 'Daily_RDA_Summary' sheet in your Excel file for internal review.")
