import streamlit as st
import pandas as pd
import os
import numpy as np
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

st.set_page_config(page_title="Narayan Farms Bio-Strategist", page_icon="🐾", layout="wide")

# --- CONFIGURATION ---
FILE_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh' 
LOCAL_FILE = "master_animal_list.xlsx"

# --- EXHAUSTIVE BREED DICTIONARY (Strict Filtering) ---
BREED_MAP = {
    "Cow (गाय)": ["Gir (गीर)", "Sahiwal (साहिवाल)", "Red Sindhi (लाल सिंधी)", "Jersey (जर्सी)", "HF (एच.एफ.)", "Deoni (देवणी)", "Khillar (खिल्लार)", "Punganur (पुंगनूर)", "Tharparkar (थारपारकर)"],
    "Buffalo (म्हैस)": ["Murrah (मुरा)", "Jaffrabadi (जाफ्राबादी)", "Pandharpuri (पंढरपुरी)", "Mehsana (महेसाणा)", "Surti (सुरती)", "Nili-Ravi (निली-रावी)"],
    "Mithun (मिथुन)": ["Nagaland Type", "Arunachal Type", "Mizoram Type", "Manipur Type"],
    "Goat (シェळी)": ["Osmanabadi (उस्मानाबादी)", "Sirohi (सिरोही)", "Boer (बोअर)", "Jamunapari (जमुनापारी)", "Barbari (बरबरी)", "Beetal (बीटल)", "Sangamneri (संगमनेरी)", "Konkan Kanyal (कोंकण कन्याळ)"],
    "Sheep (मेंढी)": ["Deccani (दख्खनी)", "Nellore (नेल्लोर)", "Marwari (मारवाडी)", "Madras Red (मद्रास रेड)", "Gaddi (गड्डी)"],
    "Hare (ससा)": ["New Zealand White", "Soviet Chinchilla", "Grey Giant", "Dutch Rabbit"],
    "Broiler Chicken (ब्रॉयलर)": ["Cobb 500", "Ross 308", "Hubbard", "Vencobb"],
    "Turkey (टर्की)": ["Broad Breasted White", "Beltsville Small White", "Bourbon Red"],
    "Chinese Fowl (चिनी कोंबडी)": ["Silkie (सिल्की)", "Cochin (कोचीन)", "Brahma (ब्रह्मा)"],
    "Desi Chicken (देशी)": ["Aseel (असील)", "Giriraja (गिरीराजा)", "Gramapriya (ग्रामप्रिया)", "Pratapdhan (प्रतापधन)"],
    "Quail (लावा)": ["Japanese Quail", "Bobwhite Quail", "Rain Quail"],
    "Kadaknath (कडकनाथ)": ["Jet Black (शुद्ध काळा)", "Pencilled (पेन्सिल)", "Golden (सोनेरी)"],
    "Other": ["Custom Breed"]
}

# --- DATA OPERATIONS ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        service.files().update(fileId=FILE_ID, media_body=media, supportsAllDrives=True).execute()
        st.sidebar.success("✅ Cloud Sync Success")
    except Exception as e:
        st.sidebar.error(f"Sync Error: {e}")

def save_to_excel(entry_df, food_df, water_df):
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        entry_df.to_excel(writer, sheet_name="Entry", index=False)
        food_df.to_excel(writer, sheet_name="Food_Log", index=False)
        water_df.to_excel(writer, sheet_name="Water_Log", index=False)
    sync_to_drive()

def load_sheet(sheet_name, columns):
    try:
        return pd.read_excel(LOCAL_FILE, sheet_name=sheet_name)
    except:
        return pd.DataFrame(columns=columns)

# --- UI ---
st.title("🚜 Narayan Farms: Expert ERP")
tab1, tab2, tab3, tab4 = st.tabs(["📝 Entry", "🍴 Food", "💧 Water", "📊 RDA Check"])

# LOAD DATA
df_entry = load_sheet("Entry", ["Name", "ID_Number", "Species", "Breed", "Sex", "Status", "Appearance", "Coat_Color"])
df_food = load_sheet("Food_Log", ["Timestamp", "Name", "Feed_Type", "Qty_g"])
df_water = load_sheet("Water_Log", ["Timestamp", "Name", "Qty_ml"])

with tab1:
    st.subheader("New Animal Entry (नवीन नोंदणी)")
    with st.form("reg_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Name (नाव)")
        id_no = c2.text_input("ID Number (ओळख क्रमांक)")
        species = c3.selectbox("Species (प्रकार)", list(BREED_MAP.keys()))
        
        # Correctly Filtered Breed List
        breed = c1.selectbox("Breed (जात)", BREED_MAP[species] + ["Custom / Other"])
        custom_b = c1.text_input("Type Breed") if breed == "Custom / Other" else ""
        
        sex = c2.selectbox("Sex (लिंग)", ["Male (नर)", "Female (मादी)", "Castrated (खच्ची)"])
        status = c3.selectbox("Status (स्थिती)", ["Juvenile (पिल्लू)", "Adult Normal", "Adult Pregnant", "Adult Lactating", "Adult Unwell", "Custom"])
        c_status = c3.text_input("Enter Status") if status == "Custom" else ""
        
        color = c1.selectbox("Color (रंग)", ["Black", "White", "Brown", "Ash", "Custom"])
        c_color = c1.text_input("Enter Color") if color == "Custom" else ""
        appearance = c2.text_area("Appearance (वर्णन)")

        if st.form_submit_button("REGISTER"):
            new_row = [name, id_no, species, custom_b or breed, sex, c_status or status, appearance, c_color or color]
            df_entry.loc[len(df_entry)] = new_row
            save_to_excel(df_entry, df_food, df_water)
            st.success(f"{name} registered in Entry sheet!")

with tab2:
    st.subheader("Food Log (चारा नोंदणी)")
    with st.form("food_form"):
        targets = st.multiselect("Select Animals", df_entry["Name"].tolist())
        feed = st.selectbox("Feed Type", ["Lucerne", "Maize", "Kadba", "Poultry Mash", "Custom"])
        c_feed = st.text_input("Custom Feed Name") if feed == "Custom" else ""
        qty = st.number_input("Qty (grams)", min_value=1)
        if st.form_submit_button("LOG FOOD"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for t in targets:
                df_food.loc[len(df_food)] = [ts, t, c_feed or feed, qty]
            save_to_excel(df_entry, df_food, df_water)
            st.success("Food Logged with Timestamp!")

with tab3:
    st.subheader("Water Log (पाणी नोंदणी)")
    with st.form("water_form"):
        w_targets = st.multiselect("Select Animals", df_entry["Name"].tolist(), key="wm")
        w_qty = st.number_input("Qty (ml)", min_value=1)
        if st.form_submit_button("LOG WATER"):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for t in w_targets:
                df_water.loc[len(df_water)] = [ts, t, w_qty]
            save_to_excel(df_entry, df_food, df_water)
            st.success("Water Logged with Timestamp!")

with tab4:
    st.subheader("Daily RDA Satisfaction (दैनिक पूर्तता)")
    today = datetime.now().strftime("%Y-%m-%d")
    # Basic logic: If food > 2000g (Cattle) or 100g (Poultry), RDA is met.
    if not df_food.empty:
        df_food['Date'] = df_food['Timestamp'].str[:10]
        daily_summary = df_food[df_food['Date'] == today].groupby('Name')['Qty_g'].sum().reset_index()
        
        def check_rda(row):
            # This is a placeholder logic based on species type
            return "✅ Satisfied" if row['Qty_g'] > 500 else "⚠️ Pending"
        
        daily_summary['RDA_Status'] = daily_summary.apply(check_rda, axis=1)
        st.table(daily_summary)
    else:
        st.info("No logs for today.")

st.sidebar.markdown("### Master Entry List")
st.sidebar.dataframe(df_entry[["Name", "Species", "Breed"]])
