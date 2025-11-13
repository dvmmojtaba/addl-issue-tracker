import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------- CONFIG ----------
DATA_FILE = "shared_issues.xlsx"  # Shared Excel file for both users

# ---------- STATIC DROPDOWNS ----------
lab_sections = [
    "Avian", "Bacteriology", "Canine Genetics", "Contracted Tests", "Histology",
    "IHC - Obsolete DON'T USE", "Molecular Diagnostics", "Other Services",
    "Parasitology", "Pathology", "Proficiency Tests", "Serology", "SIPAC Avian",
    "SIPAC Bacteriology", "SIPAC Parasitology", "SIPAC Virology",
    "Special Stains-Obsolete", "Toxicology", "TSE", "Virology"
]

species_list = [
    "Cervid", "Avian", "Bovine", "Canine", "Equine", "Feline", "Caprine",
    "Lab An.", "Camelid", "Non An.", "Ovine", "Porcine", "Aquatic",
    "Unspecified", "Unknown", "Miscellaneous"
]

mailing_room_issues = [
    "Missing Sample", "Missing Submission Form", "Broken Sample", "Broken Box",
    "Inappropriate Specimen", "No/Incorrect Test Marked", "No/Incorrect Species Marked",
    "No History", "Blank Submission Form", "No/Incorrect Premise ID", "Check",
    "No Owner", "No Vet", "Test Suggestion", "Other"
]

client_comm_issues = [
    "Result Interpretation", "Turnaround Time", "Sample Submission",
    "Consultation for Testing", "Fees", "Other"
]

# ---------- INITIALIZATION ----------
if not os.path.exists(DATA_FILE):
    # Create an empty DataFrame with predefined columns
    df = pd.DataFrame(columns=[
        "Issue ID", "Date Reported", "Reported By", "Category", "Subcategory",
        "Lab Section", "Species", "Description", "Action Taken",
        "Resolution Date", "Notes"
    ])
    df.to_excel(DATA_FILE, index=False)

# Load existing issues
df = pd.read_excel(DATA_FILE)

# Keep only the columns that match the Add New Issue form
expected_columns = [
    "Issue ID", "Date Reported", "Reported By", "Category", "Subcategory",
    "Lab Section", "Species", "Description", "Action Taken",
    "Resolution Date", "Notes"
]
df = df[expected_columns]

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="ADDL Issue Tracker", layout="wide")
st.title("🐄 ADDL Issue Tracker")
st.markdown("Let's log, track, and resolve issues!")

# ---------- SIDEBAR ----------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Add New Issue", "View Issues", "Analytics Dashboard"])

# ---------- ADD NEW ISSUE ----------
if page == "Add New Issue":
    st.subheader("📝 Add a New Issue")

    # Initialize session state for showing success message and form reset
    if 'show_success' not in st.session_state:
        st.session_state.show_success = False
    if 'last_issue_id' not in st.session_state:
        st.session_state.last_issue_id = None
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0
    
    # Show success message if issue was just added
    if st.session_state.show_success:
        st.success(f"✅ Issue #{st.session_state.last_issue_id} added successfully!")
        st.balloons()
        st.session_state.show_success = False
        st.session_state.form_key += 1  # Increment to clear all fields

    # Category selection with unique key
    reported_by = st.text_input("Reported By (Your Name)", key=f"reported_by_{st.session_state.form_key}")
    category = st.selectbox("Category *", ["— Select —", "Mailing Room", "Client Communication", "Lab Section", "Other"], key=f"category_{st.session_state.form_key}")

    # Subcategory pickers appear dynamically based on category selection
    subcategory = []
    if category == "Mailing Room":
        subcategory = st.multiselect("Mailing Room Issue Type(s) *", mailing_room_issues, key=f"subcategory_mr_{st.session_state.form_key}")
    elif category == "Client Communication":
        subcategory = st.multiselect("Client Communication Issue Type(s) *", client_comm_issues, key=f"subcategory_cc_{st.session_state.form_key}")
    elif category == "Lab Section":
        st.info("💡 For Lab Section issues, please select the relevant lab section(s) below and describe the issue.")
    elif category == "Other":
        st.info("💡 Please provide details in the Description field below.")

    # Rest of the form with unique keys
    st.markdown("---")
    lab_section = st.multiselect("Lab Section(s) (Optional)", lab_sections, key=f"lab_section_{st.session_state.form_key}")
    species = st.multiselect("Species Involved (Optional)", species_list, key=f"species_{st.session_state.form_key}")

    st.markdown("---")
    description = st.text_area("Issue Description *", help="Required: Describe the issue in detail", key=f"description_{st.session_state.form_key}")
    action_taken = st.text_area("Action Taken (if any)", key=f"action_taken_{st.session_state.form_key}")
    resolution_date = st.date_input("Resolution Date (if resolved)", value=None, key=f"resolution_date_{st.session_state.form_key}")
    notes = st.text_area("Notes or Comments", key=f"notes_{st.session_state.form_key}")

    # Submit button
    if st.button("Add Issue", type="primary", use_container_width=True):
        if category == "— Select —":
            st.error("⚠️ Please select a Category before adding the issue.")
        elif not description.strip():
            st.error("⚠️ Please provide an Issue Description.")
        elif category in ["Mailing Room", "Client Communication"] and not subcategory:
            st.error(f"⚠️ Please select at least one subcategory for {category}.")
        else:
            # Show processing message
            with st.spinner("Adding issue..."):
                new_issue = {
                    "Issue ID": len(df) + 1,
                    "Date Reported": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Reported By": reported_by,
                    "Category": category,
                    "Subcategory": ", ".join(subcategory) if subcategory else "",
                    "Lab Section": ", ".join(lab_section) if lab_section else "",
                    "Species": ", ".join(species) if species else "",
                    "Description": description,
                    "Action Taken": action_taken,
                    "Resolution Date": resolution_date.strftime("%Y-%m-%d") if resolution_date else "",
                    "Notes": notes
                }

                # Append new issue and save
                df = pd.concat([df, pd.DataFrame([new_issue])], ignore_index=True)
                df.to_excel(DATA_FILE, index=False)
                
                # Store issue ID for success message
                st.session_state.last_issue_id = len(df)
                st.session_state.show_success = True
            
            # Rerun to show success and clear form
            st.rerun()

# ---------- View Issues ----------
elif page == "View Issues":
    st.subheader("📋 All Issues")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input("🔍 Search by keyword:", placeholder="Type to filter issues...")
    with col2:
        if st.button("🔄 Refresh Data"):
            df = pd.read_excel(DATA_FILE)
            # Keep only expected columns
            df = df[expected_columns]
            st.success("Data refreshed!")
    with col3:
        # Download button
        from io import BytesIO
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        buffer.seek(0)
        
        st.download_button(
            label="📥 Download",
            data=buffer,
            file_name=f"issues_backup_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    if search:
        filtered = df[df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
    else:
        filtered = df
    
    if not filtered.empty:
        st.dataframe(filtered, use_container_width=True, height=500)
        st.caption(f"Showing {len(filtered)} of {len(df)} total issues")
    else:
        st.info("No issues found. Try adjusting your search or add a new issue.")

# ---------- ANALYTICS DASHBOARD ----------
elif page == "Analytics Dashboard":
    st.subheader("📊 Analytics Summary")
    
    if not df.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Issues", len(df))
        with col2:
            resolved = df["Resolution Date"].notna().sum()
            st.metric("Resolved Issues", resolved)
        with col3:
            open_issues = len(df) - resolved
            st.metric("Open Issues", open_issues)
        with col4:
            if len(df) > 0:
                resolution_rate = (resolved / len(df)) * 100
                st.metric("Resolution Rate", f"{resolution_rate:.1f}%")
        
        st.markdown("---")
        
        # Category breakdown
        st.subheader("Issues by Category")
        st.bar_chart(df["Category"].value_counts())
        
        st.markdown("---")
        
        # Lab Section and Species breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Issues by Lab Section")
            if "Lab Section" in df.columns and df["Lab Section"].notna().any():
                lab_counts = df["Lab Section"].dropna().str.split(", ").explode().value_counts()
                st.bar_chart(lab_counts)
            else:
                st.info("No lab section data available yet.")
        
        with col2:
            st.subheader("Issues by Species")
            if "Species" in df.columns and df["Species"].notna().any():
                species_counts = df["Species"].dropna().str.split(", ").explode().value_counts()
                st.bar_chart(species_counts)
            else:
                st.info("No species data available yet.")
    else:
        st.info("📭 No data yet. Start by adding your first issue!")
