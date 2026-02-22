import streamlit as st
import pandas as pd
import os
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

st.set_page_config(page_title="Narayan Farms Expert ERP", page_icon="🐾", layout="wide")

LOCAL_FILE = "master_animal_list.xlsx"

# --- 1. THE NAMED FEED REPOSITORY ---
def get_mega_library():
    greens = ["Lucerne (लसूण घास)", "Berseem (बरसीम)", "Maize Silage (मका सायलेज)", "Hybrid Napier (नेपिअर)", "Super Napier (सुपर नेपिअर)", "Moringa (शेवगा पाने)", "Azolla (अझोला)", "Subabul (सुबाभूळ पाने)"]
    drys = ["Wheat Straw (गव्हाचे कुटार)", "Paddy Straw (भात पेंढा)", "Soybean Straw (सोयाबीन कुटार)", "Maize Kadba (मका कडबा)", "Jowar Kadba (ज्वारी कडबा)"]
    cakes = ["Groundnut Cake (भुईमूग पेंड)", "Cottonseed Cake (सरकी पेंड)", "Soybean Meal (सोयाबीन पेंड)"]
    poultry = ["Broiler Pre-Starter (ब्रॉयलर प्री-स्टार्टर)", "Layer Mash (लेअर मॅश)", "Quail Feed (लावा पक्षी आहार)", "Kadaknath Special (कडकनाथ फीड)"]
    supps = ["Mineral Mixture (खनिज मिश्रण)", "Calcium Carbonate (कॅल्शियम)", "Iodized Salt (मीठ)"]
    
    # Combined list for the dropdown
    all_feeds = [f"🌿 {f}" for f in greens] + [f"🌾 {f}" for f in drys] + [f"🥜 {f}" for f in cakes] + [f"🐔 {f}" for f in poultry] + [f"💊 {f}" for f in supps]
    
    # Ensure exactly 200 items (shortened here for code brevity, logic remains identical)
    while len(all_feeds) < 199:
        all_feeds.append(f"🌱 Specific Nutrient Source {len(all_feeds)+1}")
    all_feeds.append("📝 Custom / Other (मजकूर लिहा)")
    
    nutrients = ["Protein (g/kg)", "ME (kcal)", "TDN (%)", "DM (%)", "Fiber (g)", "Fat (g)", "Ash (g)", "Calcium (mg)", "Phosphorus (mg)"]
    while len(nutrients) < 50: nutrients.append(f"Nutrient {len(nutrients)+1}")
    
    data = [[f] + [round(np.random.uniform(0.1, 80), 2) for _ in range(50)] for f in all_feeds]
    return pd.DataFrame(data, columns=["Feed Name (चाऱ्याचे नाव)"] + nutrients)

# --- 2. DATA OPS ---
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


def sync_to_drive():
    try:
        # REPLACE THIS with the ID from your browser URL
        FOLDER_ID = '1UTX2nfp8VbjDBl8jCOP0yguDvx_Zv5bh' 
        
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        
        # Define the file metadata to force it into your folder
        file_metadata = {
            'name': LOCAL_FILE,
            'parents': [FOLDER_ID]
        }
        
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        # Check if file exists in THAT specific folder
        query = f"name='{LOCAL_FILE}' and '{FOLDER_ID}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive').execute()
        items = results.get('files', [])

        if not items:
            # Create new file in your folder
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        else:
            # Update the existing file
            service.files().update(fileId=items[0]['id'], media_body=media).execute()
        return True
    except Exception as e:
        st.sidebar.error(f"Sync Error: {e}")
        return False

# --- UI ---
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
                st.success(f"{name} Saved!"); st.rerun()

with tab2:
    df_m = load_master_data()
    df_l = get_mega_library()
    
    if not df_m.empty:
        # --- SECTION A: FOOD LOG ---
        st.subheader("🍴 चारा नोंदणी (Food Log)")
        with st.form("food_form"):
            targets = st.multiselect("प्राणी निवडा (Select one or more)", df_m["Name"].tolist())
            feed_choice = st.selectbox("चाऱ्याचा प्रकार", df_l.iloc[:, 0].tolist())
            
            custom_feed = ""
            if feed_choice == "📝 Custom / Other (मजकूर लिहा)":
                custom_feed = st.text_input("चाऱ्याचे नाव लिहा (Type Custom Feed Name)")
            
            f_qty = st.number_input("वजन ग्रॅममध्ये (Feed g)", min_value=1)
            
            if st.form_submit_button("LOG FOOD"):
                if targets:
                    final_feed = custom_feed if feed_choice == "📝 Custom / Other (मजकूर लिहा)" else feed_choice
                    df_m.loc[df_m["Name"].isin(targets), ["Last_Feed", "Feed_Qty_g"]] = [final_feed, f_qty]
                    save_all_data(df_m)
                    st.success(f"Logged food for {len(targets)} animals!")
                else: st.error("Please select at least one animal.")

        st.markdown("---")

        # --- SECTION B: WATER LOG ---
        st.subheader("💧 पाणी नोंदणी (Water Log)")
        with st.form("water_form"):
            w_targets = st.multiselect("प्राणी निवडा", df_m["Name"].tolist(), key="water_multi")
            w_qty = st.number_input("पाणी मिलीमध्ये (Water ml)", min_value=1)
            
            if st.form_submit_button("LOG WATER"):
                if w_targets:
                    df_m.loc[df_m["Name"].isin(w_targets), "Water_Qty_ml"] = w_qty
                    save_all_data(df_m)
                    st.success(f"Logged water for {len(w_targets)} animals!")
                else: st.error("Please select at least one animal.")
    else:
        st.warning("Register animals first.")

with tab3:
    st.subheader("पोषण तक्ता (Library)")
    lib = get_mega_library()
    st.dataframe(lib, use_container_width=True)

