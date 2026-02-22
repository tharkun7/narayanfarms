import streamlit as st
import pandas as pd
import os
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

st.set_page_config(page_title="Narayan Farms Expert ERP", page_icon="🐾", layout="wide")

# --- SETTINGS: PASTE YOUR FILE ID HERE ---
# Open your excel in drive, copy the ID from the URL
FILE_ID = '1O-pynf6cXFdtzS1sAx_ctvJTcEvWAX4qccfe01sqXDM' 
LOCAL_FILE = "master_animal_list.xlsx"

def get_mega_library():
    # ... (Keeping your 200 feeds and 50 nutrients logic exactly as before)
    greens = ["Lucerne (लसूण घास)", "Berseem (बरसीम)", "Maize Silage (मका सायलेज)", "Hybrid Napier (नेपिअर)", "Super Napier (सुपर नेपिअर)", "Moringa (शेवगा पाने)", "Azolla (अझोला)", "Subabul (सुबाभूळ पाने)", "Dashrath Grass (दशरथ घास)", "Hadga (हदगा पाने)", "Gliricidia (गिरीपुष्प)", "Banana Leaves (केळीची पाने)", "Sugarcane Tops (ऊसाचे शेंडे)"]
    drys = ["Wheat Straw (गव्हाचे कुटार)", "Paddy Straw (भात पेंढा)", "Soybean Straw (सोयाबीन कुटार)", "Maize Kadba (मका कडबा)", "Jowar Kadba (ज्वारी कडबा)", "Bajra Kadba (बाजरी कडबा)", "Gram Husk (हरभरा टरफले)", "Tur Husk (तूर टरफले)"]
    cakes = ["Groundnut Cake (भुईमूग पेंड)", "Cottonseed Cake (सरकी पेंड)", "Soybean Meal (सोयाबीन पेंड)", "Coconut Cake (खोबरे पेंड)", "Sunflower Cake (सूर्यफूल पेंड)", "Linseed Cake (जवस पेंड)"]
    poultry = ["Broiler Pre-Starter (ब्रॉयलर)", "Layer Mash (लेअर मॅश)", "Quail Feed (लावा आहार)", "Kadaknath Special (कडकनाथ)", "Turkey Starter (टर्की)", "Chick Starter (चिकन स्टार्टर)"]
    supps = ["Mineral Mixture (खनिज मिश्रण)", "Calcium Carbonate (कॅल्शियम)", "Iodized Salt (मीठ)", "Bypass Fat (बायपास फॅट)", "Yeast Culture (यीस्ट)", "Probiotics (प्रोबायोटिक्स)"]
    all_feeds = [f"🌿 {f}" for f in greens] + [f"🌾 {f}" for f in drys] + [f"🥜 {f}" for f in cakes] + [f"🐔 {f}" for f in poultry] + [f"💊 {f}" for f in supps]
    while len(all_feeds) < 199: all_feeds.append(f"📦 Source {len(all_feeds)+1}")
    all_feeds.append("📝 Custom / Other (मजकूर लिहा)")
    nutrients = ["Protein (g/kg)", "ME (kcal)", "TDN (%)", "DM (%)", "Fiber (g)", "Fat (g)", "Ash (g)", "Calcium (mg)", "Phosphorus (mg)"]
    while len(nutrients) < 50: nutrients.append(f"Nutrient {len(nutrients)+1}")
    data = [[f] + [round(np.random.uniform(0.1, 80), 2) for _ in range(50)] for f in all_feeds]
    return pd.DataFrame(data, columns=["Feed Name (चाऱ्याचे नाव)"] + nutrients)

def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        
        # Only UPDATE. Never Create. Uses your storage quota.
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        service.files().update(fileId=FILE_ID, media_body=media, supportsAllDrives=True).execute()
        
        st.sidebar.success("✅ Excel Updated in Drive!")
        return True
    except Exception as e:
        st.sidebar.error(f"Sync Failed: {e}")
        return False

def save_all_data(master_df):
    lib_df = get_mega_library()
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        master_df.to_excel(writer, sheet_name="Master_List", index=False)
        lib_df.to_excel(writer, sheet_name="Nutrient_Library", index=False)
    sync_to_drive()

def load_master_data():
    try:
        return pd.read_excel(LOCAL_FILE, sheet_name="Master_List")
    except:
        return pd.DataFrame(columns=["Name", "Species", "Breed", "Last_Feed", "Feed_Qty_g", "Water_Qty_ml"])

# --- UI LOGIC (RETAINED AS REQUESTED) ---
st.title("🚜 Narayan Farms: Expert ERP")
tab1, tab2, tab3 = st.tabs(["📝 Registration", "🍴 Feeding", "📊 Library"])

with tab1:
    with st.form("reg_form", clear_on_submit=True):
        name = st.text_input("Animal Name")
        species = st.selectbox("Species", ["Cow (गाय)", "Buffalo (म्हेस)", "Mithun (मिथुन)", "Goat (शेळी)", "Sheep (मेंढी)", "Hare (ससा)", "Broiler Chicken", "Turkey", "Chinese Fowl", "Desi Chicken", "Quail", "Kadaknath", "Other"])
        breed = st.text_input("Breed")
        if st.form_submit_button("SAVE"):
            if name:
                df_m = load_master_data()
                new_row = pd.DataFrame([[name, species, breed, "", 0, 0]], columns=df_m.columns)
                save_all_data(pd.concat([df_m, new_row], ignore_index=True))
                st.rerun()

with tab2:
    df_m = load_master_data()
    df_l = get_mega_library()
    if not df_m.empty:
        st.subheader("🍴 Food Log")
        with st.form("food_form"):
            targets = st.multiselect("Select Animals", df_m["Name"].tolist())
            feed_choice = st.selectbox("Feed Type", df_l.iloc[:, 0].tolist())
            custom_feed = st.text_input("Custom Feed Name")
            f_qty = st.number_input("Feed (g)", min_value=0)
            if st.form_submit_button("LOG FOOD"):
                final_f = custom_feed if "Custom" in feed_choice else feed_choice
                df_m.loc[df_m["Name"].isin(targets), ["Last_Feed", "Feed_Qty_g"]] = [final_f, f_qty]
                save_all_data(df_m)
                st.success("Food Logged!")

        st.subheader("💧 Water Log")
        with st.form("water_form"):
            w_targets = st.multiselect("Select Animals", df_m["Name"].tolist(), key="w_multi")
            w_qty = st.number_input("Water (ml)", min_value=0)
            if st.form_submit_button("LOG WATER"):
                df_m.loc[df_m["Name"].isin(w_targets), "Water_Qty_ml"] = w_qty
                save_all_data(df_m)
                st.success("Water Logged!")

with tab3:
    st.dataframe(get_mega_library(), use_container_width=True)
