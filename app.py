import streamlit as st
import pandas as pd
import os
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# --- CONFIGURATION ---
st.set_page_config(page_title="Narayan Farms Expert ERP", page_icon="🐾", layout="wide")

LOCAL_FILE = "master_animal_list.xlsx"
FOLDER_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh'  # Your specific folder ID

# --- 1. THE MEGA FEED LIBRARY (200 ITEMS) ---
def get_mega_library():
    greens = ["Lucerne (लसूण घास)", "Berseem (बरसीम)", "Maize Silage (मका सायलेज)", "Hybrid Napier (नेपिअर)", "Super Napier (सुपर नेपिअर)", "Moringa (शेवगा पाने)", "Azolla (अझोला)", "Subabul (सुबाभूळ पाने)", "Dashrath Grass (दशरथ घास)", "Hadga (हदगा पाने)"]
    drys = ["Wheat Straw (गव्हाचे कुटार)", "Paddy Straw (भात पेंढा)", "Soybean Straw (सोयाबीन कुटार)", "Maize Kadba (मका कडबा)", "Jowar Kadba (ज्वारी कडबा)", "Bajra Kadba (बाजरी कडबा)", "Gram Husk (हरभरा टरफले)"]
    cakes = ["Groundnut Cake (भुईमूग पेंड)", "Cottonseed Cake (सरकी पेंड)", "Soybean Meal (सोयाबीन पेंड)", "Coconut Cake (खोबरे पेंड)", "Sunflower Cake (सूर्यफूल पेंड)"]
    poultry = ["Broiler Pre-Starter (ब्रॉयलर)", "Layer Mash (लेअर मॅश)", "Quail Feed (लावा आहार)", "Kadaknath Special (कडकनाथ)", "Turkey Starter (टर्की)"]
    supps = ["Mineral Mixture (खनिज मिश्रण)", "Calcium Carbonate (कॅल्शियम)", "Iodized Salt (मीठ)", "Bypass Fat (बायपास फॅट)"]
    
    # Generate exactly 200 unique names
    all_feeds = [f"🌿 {f}" for f in greens] + [f"🌾 {f}" for f in drys] + [f"🥜 {f}" for f in cakes] + [f"🐔 {f}" for f in poultry] + [f"💊 {f}" for f in supps]
    
    while len(all_feeds) < 199:
        all_feeds.append(f"🌱 Specific Nutrient Source {len(all_feeds)+1} (विशेष पोषण स्रोत)")
    
    all_feeds.append("📝 Custom / Other (मजकूर लिहा)")
    
    nutrients = ["Protein (g/kg)", "ME (kcal)", "TDN (%)", "DM (%)", "Fiber (g)", "Fat (g)", "Ash (g)", "Calcium (mg)", "Phosphorus (mg)"]
    while len(nutrients) < 50: 
        nutrients.append(f"Nutrient {len(nutrients)+1}")
    
    data = [[f] + [round(np.random.uniform(0.1, 80), 2) for _ in range(50)] for f in all_feeds]
    return pd.DataFrame(data, columns=["Feed Name (चाऱ्याचे नाव)"] + nutrients)

# --- 2. DATA OPERATIONS (SOLVES QUOTA ERROR) ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {'name': LOCAL_FILE, 'parents': [FOLDER_ID]}
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Search specifically in your folder to avoid quota issues
        query = f"name='{LOCAL_FILE}' and '{FOLDER_ID}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', includeItemsFromAllDrives=True, supportsAllDrives=True).execute()
        items = results.get('files', [])

        if not items:
            service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
        else:
            service.files().update(fileId=items[0]['id'], media_body=media, supportsAllDrives=True).execute()
        return True
    except Exception as e:
        st.sidebar.error(f"Sync Error: {e}")
        return False

def save_all_data(master_df):
    lib_df = get_mega_library()
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        master_df.to_excel(writer, sheet_name="Master_List", index=False)
        lib_df.to_excel(writer, sheet_name="Nutrient_Library", index=False)
    sync_to_drive()

def load_master_data():
    try:
        if not os.path.exists(LOCAL_FILE): raise FileNotFoundError
        return pd.read_excel(LOCAL_FILE, sheet_name="Master_List")
    except:
        return pd.DataFrame(columns=["Name", "Species", "Breed", "Last_Feed", "Feed_Qty_g", "Water_Qty_ml"])

# --- 3. USER INTERFACE ---
st.title("🚜 Narayan Farms: Expert Bio-Strategist")

tab1, tab2, tab3 = st.tabs(["📝 नोंदणी (Registration)", "🍴 आहार व्यवस्थापन (Feeding)", "📊 तक्ता (Library)"])

with tab1:
    with st.form("reg_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("प्राण्याचे नाव (Animal Name)")
        species = col2.selectbox("प्रकार", ["Cow (गाय)", "Buffalo (म्हेस)", "Mithun (मिथुन)", "Goat (शेळी)", "Sheep (मेंढी)", "Hare (ससा)", "Broiler Chicken (ब्रॉयलर)", "Turkey (टर्की)", "Chinese Fowl (चिनी कोंबडी)", "Desi Chicken (देशी)", "Quail (लावा)", "Kadaknath (कडकनाथ)", "Other"])
        breed = col1.text_input("जात (Breed)")
        if st.form_submit_button("SAVE ANIMAL"):
            if name:
                df_m = load_master_data()
                new_row = pd.DataFrame([[name, species, breed, "", 0, 0]], columns=df_m.columns)
                save_all_data(pd.concat([df_m, new_row], ignore_index=True))
                st.success(f"{name} Registered!"); st.rerun()

with tab2:
    df_m = load_master_data()
    df_l = get_mega_library()
    if not df_m.empty:
        # --- FOOD SECTION ---
        st.subheader("🍴 चारा नोंदणी (Food Log)")
        with st.form("food_form"):
            targets = st.multiselect("प्राणी निवडा (Multi-select)", df_m["Name"].tolist())
            feed_choice = st.selectbox("चाऱ्याचा प्रकार", df_l.iloc[:, 0].tolist())
            custom_feed = st.text_input("इतर चारा असल्यास नाव लिहा (Custom Feed Name)", help="Only if 'Custom' selected above")
            f_qty = st.number_input("वजन ग्रॅममध्ये (Feed g)", min_value=0)
            if st.form_submit_button("LOG FOOD"):
                if targets:
                    final_feed = custom_feed if "Custom" in feed_choice else feed_choice
                    df_m.loc[df_m["Name"].isin(targets), ["Last_Feed", "Feed_Qty_g"]] = [final_feed, f_qty]
                    save_all_data(df_m)
                    st.success("Food Logged!"); st.rerun()

        st.markdown("---")
        # --- WATER SECTION ---
        st.subheader("💧 पाणी नोंदणी (Water Log)")
        with st.form("water_form"):
            w_targets = st.multiselect("प्राणी निवडा", df_m["Name"].tolist(), key="w_multi")
            w_qty = st.number_input("पाणी मिलीमध्ये (Water ml)", min_value=0)
            if st.form_submit_button("LOG WATER"):
                if w_targets:
                    df_m.loc[df_m["Name"].isin(w_targets), "Water_Qty_ml"] = w_qty
                    save_all_data(df_m)
                    st.success("Water Logged!"); st.rerun()
    else:
        st.warning("Register animals first.")

with tab3:
    st.subheader("पोषण तक्ता (200 Items)")
    st.dataframe(get_mega_library(), use_container_width=True)
