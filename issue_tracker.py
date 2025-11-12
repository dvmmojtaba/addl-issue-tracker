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

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="ADDL Issue Tracker", layout="wide")
st.title("🐄 ADDL Issue Tracker")
st.markdown("Log, track, and resolve issues collaboratively with your supervisor.")

# ---------- SIDEBAR ----------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Add New Issue", "View / Edit Issues", "Analytics Dashboard"])

# ---------- ADD NEW ISSUE ----------
if page == "Add New Issue":
    st.subheader("📝 Add a New Issue")

    # Category selection OUTSIDE the form so it can trigger dynamic content
    reported_by = st.text_input("Reported By (Your Name)")
    category = st.selectbox("Category *", ["— Select —", "Mailing Room", "Client Communication", "Lab Section", "Other"])

    # Subcategory pickers appear dynamically based on category selection
    subcategory = []
    if category == "Mailing Room":
        subcategory = st.multiselect("Mailing Room Issue Type(s) *", mailing_room_issues)
    elif category == "Client Communication":
        subcategory = st.multiselect("Client Communication Issue Type(s) *", client_comm_issues)
    elif category == "Lab Section":
        st.info("💡 For Lab Section issues, please select the relevant lab section(s) below and describe the issue.")
    elif category == "Other":
        st.info("💡 Please provide details in the Description field below.")

    # Rest of the form
    st.markdown("---")
    lab_section = st.multiselect("Lab Section(s) (Optional)", lab_sections)
    species = st.multiselect("Species Involved (Optional)", species_list)

    st.markdown("---")
    description = st.text_area("Issue Description *", help="Required: Describe the issue in detail")
    action_taken = st.text_area("Action Taken (if any)")
    resolution_date = st.date_input("Resolution Date (if resolved)", value=None)
    notes = st.text_area("Notes or Comments")

    # Submit button (not in a form anymore)
    if st.button("Add Issue", type="primary"):
        if category == "— Select —":
            st.error("⚠️ Please select a Category before adding the issue.")
        elif not description.strip():
            st.error("⚠️ Please provide an Issue Description.")
        elif category in ["Mailing Room", "Client Communication"] and not subcategory:
            st.error(f"⚠️ Please select at least one subcategory for {category}.")
        else:
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
            st.success("✅ Issue added successfully!")
            st.balloons()
            
            # Note: Fields won't auto-clear since we're not using st.form
            st.info("💡 Tip: Refresh the page to add another issue with cleared fields.")

# ---------- VIEW / EDIT ISSUES ----------
elif page == "View / Edit Issues":
    st.subheader("📋 All Issues")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Search by keyword:", placeholder="Type to filter issues...")
    with col2:
        if st.button("🔄 Refresh Data"):
            df = pd.read_excel(DATA_FILE)
            st.success("Data refreshed!")
    
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
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Issues by Category")
            st.bar_chart(df["Category"].value_counts())
        
        with col2:
            st.subheader("Issues by Reporter")
            reporter_counts = df["Reported By"].value_counts().head(10)
            st.bar_chart(reporter_counts)
        
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