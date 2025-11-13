import streamlit as st
import pandas as pd
from datetime import datetime
import io

import gspread
from google.oauth2.service_account import Credentials

# ---------- GOOGLE SHEETS SETUP ----------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# uses secrets.toml: [gcp_service_account] {...}
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES,
)
client = gspread.authorize(creds)

SHEET_NAME = "shared_issues"  # Google Sheet name (tab 1)

EXPECTED_COLUMNS = [
    "Issue ID",
    "Date Reported",
    "Reported By",
    "Category",
    "Subcategory",
    "Lab Section",
    "Species",
    "Description",
    "Action Taken",
    "Resolution Date",
    "Notes",
]


def _ensure_header(sheet):
    """Make sure the first row contains the expected header."""
    existing = sheet.row_values(1)
    if not existing:
        # Empty sheet -> write header
        sheet.insert_row(EXPECTED_COLUMNS, 1)
    else:
        # If headers differ, we still assume first row is header
        pass


def load_issues():
    """Load issues from Google Sheets into a DataFrame."""
    sheet = client.open(SHEET_NAME).sheet1
    _ensure_header(sheet)
    data = sheet.get_all_records()
    if not data:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    else:
        df = pd.DataFrame(data)
        # ensure all expected columns exist
        for col in EXPECTED_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[EXPECTED_COLUMNS]
    return df


def save_issues(df: pd.DataFrame):
    """Write the DataFrame back to Google Sheets (overwrite all rows)."""
    sheet = client.open(SHEET_NAME).sheet1
    sheet.clear()
    sheet.update(
        [EXPECTED_COLUMNS] + df[EXPECTED_COLUMNS].astype(str).values.tolist()
    )


# ---------- STATIC DROPDOWNS ----------
lab_sections = [
    "Avian",
    "Bacteriology",
    "Canine Genetics",
    "Contracted Tests",
    "Histology",
    "IHC - Obsolete DON'T USE",
    "Molecular Diagnostics",
    "Other Services",
    "Parasitology",
    "Pathology",
    "Proficiency Tests",
    "Serology",
    "SIPAC Avian",
    "SIPAC Bacteriology",
    "SIPAC Parasitology",
    "SIPAC Virology",
    "Special Stains-Obsolete",
    "Toxicology",
    "TSE",
    "Virology",
]

species_list = [
    "Cervid",
    "Avian",
    "Bovine",
    "Canine",
    "Equine",
    "Feline",
    "Caprine",
    "Lab An.",
    "Camelid",
    "Non An.",
    "Ovine",
    "Porcine",
    "Aquatic",
    "Unspecified",
    "Unknown",
    "Miscellaneous",
]

mailing_room_issues = [
    "Missing Sample",
    "Missing Submission Form",
    "Broken Sample",
    "Broken Box",
    "Inappropriate Specimen",
    "No/Incorrect Test Marked",
    "No/Incorrect Species Marked",
    "No History",
    "Blank Submission Form",
    "No/Incorrect Premise ID",
    "Check",
    "No Owner",
    "No Vet",
    "Test Suggestion",
    "Other",
]

client_comm_issues = [
    "Result Interpretation",
    "Turnaround Time",
    "Sample Submission",
    "Consultation for Testing",
    "Fees",
    "Other",
]

# ---------- LOAD DATA FROM GOOGLE SHEETS ----------
df = load_issues()

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="ADDL Issue Tracker", layout="wide")
st.title("🐄 ADDL Issue Tracker")
st.markdown("Let's log, track, and resolve issues!")

# ---------- SIDEBAR ----------
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to", ["Add New Issue", "View Issues", "Analytics Dashboard"]
)

# ---------- ADD NEW ISSUE ----------
if page == "Add New Issue":
    st.subheader("📝 Add a New Issue")

    # Initialize session state for showing success message and form reset
    if "show_success" not in st.session_state:
        st.session_state.show_success = False
    if "last_issue_id" not in st.session_state:
        st.session_state.last_issue_id = None
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0

    # Show success message if issue was just added
    if st.session_state.show_success:
        st.success(
            f"✅ Issue #{st.session_state.last_issue_id} added successfully!"
        )
        st.balloons()
        st.session_state.show_success = False
        st.session_state.form_key += 1  # Increment to clear all fields

    # Inputs with unique keys tied to form_key
    reported_by = st.text_input(
        "Reported By (Your Name)",
        key=f"reported_by_{st.session_state.form_key}",
    )
    category = st.selectbox(
        "Category *",
        ["— Select —", "Mailing Room", "Client Communication", "Lab Section", "Other"],
        key=f"category_{st.session_state.form_key}",
    )

    # Subcategory pickers appear dynamically
    subcategory = []
    if category == "Mailing Room":
        subcategory = st.multiselect(
            "Mailing Room Issue Type(s) *",
            mailing_room_issues,
            key=f"subcategory_mr_{st.session_state.form_key}",
        )
    elif category == "Client Communication":
        subcategory = st.multiselect(
            "Client Communication Issue Type(s) *",
            client_comm_issues,
            key=f"subcategory_cc_{st.session_state.form_key}",
        )
    elif category == "Lab Section":
        st.info(
            "💡 For Lab Section issues, please select the relevant lab section(s) below and describe the issue."
        )
    elif category == "Other":
        st.info("💡 Please provide details in the Description field below.")

    st.markdown("---")
    lab_section = st.multiselect(
        "Lab Section(s) (Optional)",
        lab_sections,
        key=f"lab_section_{st.session_state.form_key}",
    )
    species = st.multiselect(
        "Species Involved (Optional)",
        species_list,
        key=f"species_{st.session_state.form_key}",
    )

    st.markdown("---")
    description = st.text_area(
        "Issue Description *",
        help="Required: Describe the issue in detail",
        key=f"description_{st.session_state.form_key}",
    )
    action_taken = st.text_area(
        "Action Taken (if any)",
        key=f"action_taken_{st.session_state.form_key}",
    )
    resolution_date = st.date_input(
        "Resolution Date (if resolved)",
        value=None,
        key=f"resolution_date_{st.session_state.form_key}",
    )
    notes = st.text_area(
        "Notes or Comments", key=f"notes_{st.session_state.form_key}"
    )

    if st.button("Add Issue", type="primary", use_container_width=True):
        if category == "— Select —":
            st.error("⚠️ Please select a Category before adding the issue.")
        elif not description.strip():
            st.error("⚠️ Please provide an Issue Description.")
        elif category in ["Mailing Room", "Client Communication"] and not subcategory:
            st.error(
                f"⚠️ Please select at least one subcategory for {category}."
            )
        else:
            with st.spinner("Adding issue..."):
                # reload latest (in case someone else added meanwhile)
                df = load_issues()

                new_issue_id = int(df["Issue ID"].max()) + 1 if not df.empty else 1

                new_issue = {
                    "Issue ID": new_issue_id,
                    "Date Reported": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "Reported By": reported_by,
                    "Category": category,
                    "Subcategory": ", ".join(subcategory)
                    if subcategory
                    else "",
                    "Lab Section": ", ".join(lab_section)
                    if lab_section
                    else "",
                    "Species": ", ".join(species) if species else "",
                    "Description": description,
                    "Action Taken": action_taken,
                    "Resolution Date": resolution_date.strftime("%Y-%m-%d")
                    if resolution_date
                    else "",
                    "Notes": notes,
                }

                df = pd.concat(
                    [df, pd.DataFrame([new_issue])], ignore_index=True
                )
                save_issues(df)

                st.session_state.last_issue_id = new_issue_id
                st.session_state.show_success = True

            st.rerun()

# ---------- VIEW ISSUES ----------
elif page == "View Issues":
    st.subheader("📋 All Issues")

    # Always load latest data from Sheets
    df = load_issues()

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input(
            "🔍 Search by keyword:", placeholder="Type to filter issues..."
        )
    with col2:
        if st.button("🔄 Refresh Data"):
            df = load_issues()
            st.success("Data refreshed from Google Sheets!")
    with col3:
        # Download current view as Excel
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="📥 Download",
            data=buffer,
            file_name=f"issues_backup_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    if search:
        filtered = df[
            df.apply(
                lambda row: row.astype(str)
                .str.contains(search, case=False)
                .any(),
                axis=1,
            )
        ]
    else:
        filtered = df

    if not filtered.empty:
        st.dataframe(filtered, use_container_width=True, height=500)
        st.caption(f"Showing {len(filtered)} of {len(df)} total issues")
    else:
        st.info(
            "No issues found. Try adjusting your search or add a new issue."
        )

# ---------- ANALYTICS DASHBOARD ----------
elif page == "Analytics Dashboard":
    st.subheader("📊 Analytics Summary")

    df = load_issues()

    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Issues", len(df))
        with col2:
            resolved = df["Resolution Date"].astype(str).str.len() > 0
            resolved_count = resolved.sum()
            st.metric("Resolved Issues", int(resolved_count))
        with col3:
            open_issues = len(df) - int(resolved_count)
            st.metric("Open Issues", open_issues)
        with col4:
            if len(df) > 0:
                resolution_rate = (resolved_count / len(df)) * 100
                st.metric("Resolution Rate", f"{resolution_rate:.1f}%")

        st.markdown("---")

        st.subheader("Issues by Category")
        st.bar_chart(df["Category"].value_counts())

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Issues by Lab Section")
            if df["Lab Section"].astype(str).str.len().any():
                lab_counts = (
                    df["Lab Section"]
                    .astype(str)
                    .replace("", pd.NA)
                    .dropna()
                    .str.split(", ")
                    .explode()
                    .value_counts()
                )
                st.bar_chart(lab_counts)
            else:
                st.info("No lab section data available yet.")

        with col2:
            st.subheader("Issues by Species")
            if df["Species"].astype(str).str.len().any():
                species_counts = (
                    df["Species"]
                    .astype(str)
                    .replace("", pd.NA)
                    .dropna()
                    .str.split(", ")
                    .explode()
                    .value_counts()
                )
                st.bar_chart(species_counts)
            else:
                st.info("No species data available yet.")
    else:
        st.info("📭 No data yet. Start by adding your first issue!")
