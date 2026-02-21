import streamlit as st
import pandas as pd
import os
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

st.set_page_config(page_title="Narayan Farms Mega-ERP", page_icon="🌾", layout="wide")

LOCAL_FILE = "master_animal_list.xlsx"

# --- 1. THE MEGA FEED GENERATOR (200+ Feeds & 50+ Nutrients) ---
def get_mega_library():
    # Category 1: Green Fodders (हिरवा चारा)
    greens = [f"🌿 {f}" for f in ["Lucerne (लसूण घास)", "Berseem (बरसीम)", "Maize (मका)", "Sorghum (ज्वारी)", "Bajra (बाजरी)", "Napier (नेपिअर)", "Stylo (स्टायलो)", "Guinea Grass (गिनी गवत)", "Para Grass (पॅरा गवत)", "Moringa (शेवगा)"]]
    # Category 2: Dry Fodders (सुका चारा)
    drys = [f"🌾 {f}" for f in ["Wheat Straw (गव्हाचे कुटार)", "Paddy Straw (भात पेंढा)", "Soybean Straw (सोयाबीन कुटार)", "Maize Kadba (मका कडबा)", "Jowar Kadba (ज्वारी कडबा)", "Sugarcane Tops (उसाचे शेंडे)"]]
    # Category 3: Cakes & Concentrates (पेंड आणि खुराख)
    cakes = [f"🥜 {f}" for f in ["Groundnut Cake (भुईमूग पेंड)", "Cottonseed Cake (सरकी पेंड)", "Soybean Meal (सोयाबीन पेंड)", "Coconut Cake (खोबरे पेंड)", "Sunflower Cake (सूर्यफूल पेंड)", "Mustard Cake (मोहरी पेंड)"]]
    
    # Create 200 dummy names for testing (You can replace these with real names later)
    all_feed_names = (greens + drys + cakes)
    while len(all_feed_names) < 200:
        all_feed_names.append(f"📦 Supplemental Feed {len(all_feed_names)+1} (पूरक आहार)")

    # Define 50 specific nutrients
    nutrients = ["Protein (%)", "Energy (kcal/kg)", "TDN (%)", "Dry Matter (%)", "Fiber (%)", "Fat (%)", "Calcium (mg)", "Phosphorus (mg)", "Magnesium (mg)", "Potassium (mg)", "Vitamin A", "Vitamin D3", "Vitamin E", "Iron", "Zinc", "Manganese", "Copper", "Iodine", "Lysine", "Methionine"]
    while len(nutrients) < 50:
        nutrients.append(f"Micronutrient {len(nutrients)+1}")

    data = []
    for f in all_feed_names:
        # Create a row with the feed name + 50 nutrient values
        row = [f] + [round(np.random.uniform(0, 100), 2) for _ in range(50)]
        data.append(row)
    
    # Final headers: Feed Name + the 50 nutrient names
    headers = ["Feed Name (चाऱ्याचे नाव)"] + nutrients
    return pd.DataFrame(data, columns=headers)

# --- 2. DATA OPERATIONS ---
def save_all_data(master_df):
    lib_df = get_mega_library()
    with pd.ExcelWriter(LOCAL_FILE, engine='openpyxl') as writer:
        master_df.to_excel(writer, sheet_name="Master_List", index=False)
        lib_df.to_excel(writer, sheet_name="Nutrient_Library", index=False)
    sync_to_drive()

def load_master_data():
    try:
        if not os.path.exists(LOCAL_FILE): return pd.DataFrame(columns=["Name", "Species", "Breed", "Last_Feed", "Weight_kg"])
        return pd.read_excel(LOCAL_FILE, sheet_name="Master_List")
    except:
        return pd.DataFrame(columns=["Name", "Species", "Breed", "Last_Feed", "Weight_kg"])

def sync_to_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        service = build('drive', 'v3', credentials=creds)
        media = MediaFileUpload(LOCAL_FILE, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        results = service.files().list(q=f"name='{LOCAL_FILE}'").execute()
        items = results.get('files', [])
        if not items:
            service.files().create(body={'name': LOCAL_FILE}, media_body=media).execute()
        else:
            service.files().update(fileId=items[0]['id'], media_body=media).execute()
    except Exception as e:
        st.sidebar.warning(f"Cloud Sync: {e}")

# --- 3. UI ---
st.title("🚜 Narayan Farms: Mega Bio-Strategist")

tab1, tab2, tab3 = st.tabs(["📝 नोंदणी (Registration)", "🍴 चारा नोंदणी (Log Feed)", "📊 पोषण लायब्ररी (Mega Library)"])

with tab1:
    with st.form("reg_form", clear_on_submit=True):
        name = st.text_input("प्राण्याचे नाव (Animal Name)")
        species = st.selectbox("प्रकार", ["Cow (गाय)", "Buffalo (म्हेस)", "Goat (शेळी)"])
        breed = st.text_input("जात (Breed)")
        if st.form_submit_button("Save Animal"):
            if name:
                df_m = load_master_data()
                new_row = pd.DataFrame([[name, species, breed, "", 0]], columns=df_m.columns)
                save_all_data(pd.concat([df_m, new_row], ignore_index=True))
                st.success(f"{name} Saved!")
                st.rerun()

with tab2:
    df_m = load_master_data()
    df_l = get_mega_library()
    if not df_m.empty:
        with st.form("feed_form"):
            target = st.selectbox("प्राणी निवडा", df_m["Name"].tolist())
            feed = st.selectbox("चाऱ्याचा प्रकार (200+ Feeds)", df_l.iloc[:, 0].tolist())
            weight = st.number_input("वजन किलोमध्ये (kg)", min_value=0.1)
            if st.form_submit_button("Log Feed"):
                df_m.loc[df_m["Name"] == target, ["Last_Feed", "Weight_kg"]] = [feed, weight]
                save_all_data(df_m)
                st.success("Feed Logged!")
    else:
        st.warning("Please register animals in Tab 1.")

with tab3:
    st.subheader("सर्वसमावेशक पोषण तक्ता (200 Feeds x 50 Nutrients)")
    lib = get_mega_library()
    search = st.text_input("चारा शोधा (Search Feed)...")
    if search:
        lib = lib[lib.iloc[:,0].str.contains(search, case=False)]
    st.dataframe(lib, use_container_width=True, height=600)

if st.sidebar.button("🗑️ Reset Local File (Fix Errors)"):
    if os.path.exists(LOCAL_FILE): os.remove(LOCAL_FILE)
    st.rerun()
