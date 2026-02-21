import streamlit as st
import pandas as pd
import os
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# App Configuration
st.set_page_config(page_title="Bio-Strategist ERP", page_icon="🌿", layout="wide")

LOCAL_FILE = "master_animal_list.xlsx"

# --- DATA INITIALIZATION ---
def initialize_excel():
    """Creates the Excel file with the full Indian Feed Library if it doesn't exist."""
    if not os.path.exists(LOCAL_FILE):
        # 1. Indian Feed Library (Marathi/English)
        feeds = [
            "🌿 Lucerne (लसूण घास)", "🌾 Berseem (बरसीम)", "🌽 Maize Kadba (कडबा)", 
            "🌾 Sorghum (ज्वार)", "🌾 Bajra (बाजरी)", "🌱 Napier Grass (नेपिअर गवत)", 
            "🌾 Wheat Straw (गव्हाचा कुटार)", "🥜 Groundnut Cake (भुईमूग पेंड)",
            "🥥 Cottonseed Cake (सरकी पेंड)", "🍞 Wheat Bran (गहू चोकर)", "🌳 Moringa (शेवगा पाने)"
        ] # Note: You can expand this list back to 70+ easily
        
        nutrients = {
            "Feed_Name": feeds,
            "Protein (प्रथिने - g)": [18, 15, 8, 7, 9, 10, 3, 45, 25, 14, 22],
            "Energy (ऊर्जा - kcal)": [250, 230, 180, 190, 200, 210, 140, 320, 280, 210, 240],
            "Fiber (तंतू - g)": [25, 28, 32, 30, 28, 35, 40, 12, 20, 15, 18]
        }
        df_lib = pd.DataFrame(nutrients)
        
        # 2. Master List Structure
        df_master = pd.DataFrame(columns=["Name", "Species", "Breed", "Last_Feed", "Weight_kg", "Timestamp"])
        
        with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
            df_lib.to_excel(writer, sheet_name="Nutrient_Library", index=False)
            df_master.to_excel(writer, sheet_name="Master_List", index=False)
        return True
    return False

# --- CLOUD SYNC ---
def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        
        query = f"name='{LOCAL_FILE}'"
        results = service.files().list(q=query, spaces='drive').execute()
        items = results.get('files', [])

        if not items:
            service.files().create(body={'name': LOCAL_FILE}, media_body=media).execute()
        else:
            service.files().update(fileId=items[0]['id'], media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Cloud Sync Error: {e}")
        return False

# --- START APP ---
initialize_excel()

st.title("🚜 Bio-Strategist: Indian Farm ERP")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📝 नोंदणी (Registration)", "🍴 चारा नोंदणी (Log Feed)", "📊 पोषण तक्ता (Nutrient Chart)"])

# TAB 1: REGISTRATION
with tab1:
    st.subheader("नवीन प्राणी नोंदणी")
    with st.form("reg_form"):
        col1, col2 = st.columns(2)
        name = col1.text_input("प्राण्याचे नाव (Animal Name)")
        species = col2.selectbox("प्रकार", ["Cow (गाय)", "Buffalo (म्हैस)", "Goat (शेळी)", "Other"])
        breed = col1.text_input("जात (Breed)")
        
        if st.form_submit_button("💾 Save to Master List"):
            df_m = pd.read_excel(LOCAL_FILE, sheet_name="Master_List")
            new_row = pd.DataFrame([[name, species, breed, "", 0, pd.Timestamp.now()]], 
                                   columns=df_m.columns)
            
            with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                pd.concat([df_m, new_row]).to_excel(writer, sheet_name="Master_List", index=False)
            
            sync_to_drive()
            st.success(f"✅ {name} Registered!")

# TAB 2: FEED LOG
with tab2:
    st.subheader("दैनंदिन चारा व्यवस्थापन")
    df_m = pd.read_excel(LOCAL_FILE, sheet_name="Master_List")
    df_l = pd.read_excel(LOCAL_FILE, sheet_name="Nutrient_Library")
    
    if not df_m.empty:
        with st.form("feed_form"):
            target_animal = st.selectbox("प्राणी निवडा (Select Animal)", df_m["Name"].tolist())
            feed_type = st.selectbox("चारा निवडा (Select Feed)", df_l["Feed_Name"].tolist())
            amount = st.number_input("वजन किलोमध्ये (Weight in kg)", min_value=0.1)
            
            if st.form_submit_button("✅ Log Feed"):
                # Logic to update the Master_List with latest feed info
                df_m.loc[df_m["Name"] == target_animal, ["Last_Feed", "Weight_kg", "Timestamp"]] = [feed_type, amount, pd.Timestamp.now()]
                
                with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df_m.to_excel(writer, sheet_name="Master_List", index=False)
                
                sync_to_drive()
                st.success(f"Logged {amount}kg of {feed_type} for {target_animal}")
    else:
        st.warning("Please register animals first.")

# TAB 3: NUTRITION CHART
with tab3:
    st.subheader("चारा पोषण मूल्य लायब्ररी")
    df_l = pd.read_excel(LOCAL_FILE, sheet_name="Nutrient_Library")
    st.dataframe(df_l, use_container_width=True)
    
    st.info("This table shows nutrients per 1kg of feed. (हे तक्ता प्रति १ किलो चार्‍यासाठी पोषक तत्वे दर्शवते.)")
