import streamlit as st
import pandas as pd
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# App Configuration
st.set_page_config(page_title="Bio-Strategist ERP", page_icon="🐄")

LOCAL_FILE = "master_animal_list.xlsx"


def sync_to_drive():
    """Syncs the local Excel file to Google Drive using Streamlit Secrets."""
    try:
        # Load credentials from Streamlit's secure vault
        creds_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(creds_info)

        service = build("drive", "v3", credentials=creds)

        # Prepare the file for upload
        media = MediaFileUpload(
            LOCAL_FILE,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Check if file exists to update, else create
        query = f"name='{LOCAL_FILE}'"
        results = service.files().list(q=query, spaces="drive").execute()
        items = results.get("files", [])

        if not items:
            service.files().create(
                body={"name": LOCAL_FILE}, media_body=media
            ).execute()
        else:
            service.files().update(fileId=items[0]["id"], media_body=media).execute()
        return True
    except Exception as e:
        st.error(f"Cloud Sync Error: {e}")
        return False


# --- UI LAYOUT ---
st.title("🐄 Bio-Strategist Farm ERP")

tab1, tab2 = st.tabs(["📝 नवीन नोंदणी (Registration)", "🍴 चारा नोंदणी (Log Feed)"])

with tab1:
    st.subheader("Add New Animal")
    with st.form("reg_form", clear_on_submit=True):
        name = st.text_input("नाव (Name)")
        species = st.selectbox(
            "प्राणी (Animal)", ["Cow (गाय)", "Buffalo (म्हैस)", "Goat (शेळी)"]
        )
        breed = st.text_input("जात (Breed)")
        submitted = st.form_submit_button("💾 SAVE & SYNC")

        if submitted:
            new_data = pd.DataFrame(
                [[name, species, breed]], columns=["Name", "Species", "Breed"]
            )

            # Create file if it doesn't exist
            if not os.path.exists(LOCAL_FILE):
                new_data.to_excel(LOCAL_FILE, index=False)
            else:
                existing_df = pd.read_excel(LOCAL_FILE)
                updated_df = pd.concat([existing_df, new_data], ignore_index=True)
                updated_df.to_excel(LOCAL_FILE, index=False)

            if sync_to_drive():
                st.success(f"✅ {name} saved to Farm List and Google Drive!")

with tab2:
    st.subheader("Feed Log")
    if os.path.exists(LOCAL_FILE):
        df_m = pd.read_excel(LOCAL_FILE)
        if not df_m.empty:
            animal_list = df_m["Name"].dropna().unique().tolist()
            selected_animal = st.selectbox("Select Animal", animal_list)
            feed_weight = st.number_input("Weight (kg)", min_value=0.1)

            if st.button("✅ LOG FEED"):
                st.info(f"Logged {feed_weight}kg for {selected_animal}")
                sync_to_drive()
        else:
            st.warning("No animals registered yet.")
    else:
        st.info("Register an animal first to start logging feed.")
