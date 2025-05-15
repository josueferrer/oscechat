import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from app.core import CASE_GEN_MODEL, PATIENT_MODEL, EVAL_MODEL
from app.core.case_generator import generate_case
from app.core.ui import inject_css, feature_list, info_box

# Configure page with collapsed sidebar - hidden via CSS in ui.py
st.set_page_config(
    page_title="OSCE Chat Simulator", 
    page_icon="🩺", 
    layout="wide",
    initial_sidebar_state="collapsed"  # Options are "auto", "expanded", "collapsed"
)

# Apply all CSS from ui.py (includes sidebar hiding)
inject_css()

# App header with stethoscope and purple heart icons
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <h1 style="margin: 0;">🩺 💜 OSCE Chat Simulator</h1>
</div>
""", unsafe_allow_html=True)

# Main content in two columns
left_col, right_col = st.columns([1, 1])

with left_col:
    st.header("Exam Settings")
    
    # Language selection - now with Arabic support
    st.subheader("Language")
    language = st.selectbox(
        "Select language", 
        ["en", "ar"],
        index=0,
        format_func=lambda x: "English" if x == "en" else "العربية"
    )
    
    # Expanded medical specialties list
    specialties = [
        "Family Medicine",
        "Internal Medicine",
        "Pediatrics",
        "Surgery",
        "Emergency Medicine",
        "Obstetrics & Gynecology",
        "Psychiatry",
        "Neurology",
        "Cardiology",
        "Dermatology"
    ]
    
    # Exam Mode selection with radio buttons
    st.subheader("Exam Mode")
    exam_mode = st.radio(
        "Select exam mode",
        ["Random Cases", "Custom Cases"],
        index=0
    )
    
    # Medical Specialty - always shown regardless of mode
    st.subheader("Medical Specialty")
    category = st.selectbox(
        "Select medical specialty",
        specialties,
        index=0
    )
    
    # Conditional UI based on exam mode
    if exam_mode == "Custom Cases":
        # Chief Complaint Selection - only shown in Custom Cases mode
        st.subheader("Chief Complaint Selection")
        complaint_selection = st.radio(
            "Choose complaint selection method",
            ["Random", "Choose Specific"],
            index=0
        )
        
        # Show custom complaint input only if "Choose Specific" is selected
        if complaint_selection == "Choose Specific":
            custom_cc = st.text_input("Enter chief complaint:", placeholder="e.g. Chest pain")
        else:
            custom_cc = ""
            
        # Patient details - only shown in Custom Cases mode
        st.subheader("Patient Details")
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Patient age", min_value=1, max_value=100, value=45)
        
        with col2:
            gender = st.radio("Patient gender", ["Male", "Female", "Other"])
            
        occupation = st.text_input("Patient occupation", placeholder="e.g. Teacher")
    else:
        # In Random Cases mode, these values are auto-generated
        complaint_selection = "Random"
        custom_cc = ""
        age = 45  # Default value
        gender = "Male"  # Default value
        occupation = "Varies"  # Default value
    
    # Number of stations - always shown
    st.subheader("Number of stations")
    n_stations = st.number_input("Enter number of stations", min_value=1, max_value=10, value=3)
    
    # Minutes per station with slider - modified to start from 1
    st.subheader("Minutes per station")
    minutes = st.slider("Select minutes per station", 1, 10, 5, 1)
    
    # Advanced settings (collapsed by default)
    with st.expander("Advanced Settings", expanded=False):
        difficulty = st.select_slider(
            "Difficulty level",
            options=["Very Easy", "Easy", "Moderate", "Challenging", "Expert"],
            value="Moderate"
        )
        
        difficulty_map = {
            "Very Easy": 1, "Easy": 2, "Moderate": 3, 
            "Challenging": 4, "Expert": 5
        }
        difficulty_value = difficulty_map[difficulty]
        
        station_type = st.selectbox(
            "Station focus",
            ["Full OSCE", "History only", "Exam only"],
            index=0
        )
        
        fully_random = st.checkbox("Completely randomize all parameters", value=(exam_mode == "Random Cases"))
    
    # Start Button
    if st.button("Start Exam", type="primary", use_container_width=True):
        # Store settings in session state
        st.session_state.settings = dict(
            n=n_stations,
            minutes=minutes,
            difficulty=difficulty_value,
            station_type=station_type,
            category=category,
            custom_cc=custom_cc if complaint_selection == "Choose Specific" else "",
            age=age,
            gender=gender,
            occupation=occupation,
            fully_random=(exam_mode == "Random Cases") or fully_random,
            language=language  # Add language to settings for consistent use across stations
        )
        
        # Initialize stations and results arrays
        st.session_state.stations = []
        st.session_state.results = []
        
        # Show loading indicator
        with st.spinner(f"Preparing your OSCE exam with {n_stations} stations..."):
            # Generate all stations upfront instead of using lazy generation
            for i in range(n_stations):
                # Only use chief_override for the first station in Custom Cases mode with Specific complaint
                chief = None
                if i == 0 and exam_mode == "Custom Cases" and complaint_selection == "Choose Specific":
                    chief = custom_cc
                
                st.session_state.stations.append(
                    generate_case(
                        lang=language,
                        chief_override=chief,
                        settings=st.session_state.settings
                    )
                )
                
                # Show progress
                if n_stations > 1:
                    progress_percent = (i + 1) / n_stations
                    st.progress(progress_percent, text=f"Generating station {i+1}/{n_stations}...")
        
        st.session_state.current = 0
        st.session_state.lazy_generation = False  # Disable lazy generation since we've created all stations
        st.switch_page("pages/Exam.py")

with right_col:
    st.header("OSCE Simulation Features")
    
    # Feature list using the feature_list component with purple-themed icons
    features = [
        ("⏱️", "Timed stations with countdown timer"),
        ("🧠", "AI-powered patient simulation"),
        ("💜", "Clinical cases with detailed parameters"),
        ("💫", "Hints available for guidance"),
        ("📝", "Mandatory final diagnosis entry"),
        ("📊", "Detailed performance feedback")
    ]
    
    feature_list(features)
    
    # Information box using the info_box component
    info_box("During the exam, take a complete history, perform appropriate examinations, and formulate a diagnosis.")
    
    # Language-specific information
    if language == "ar":
        st.info("سيتم توليد الحالات باللغة العربية. يرجى ملاحظة أن هذه ميزة تجريبية.")
    
    # Model information (smaller and less prominent)
    st.markdown(f"""
    <div style="margin-top: 30px; font-size: 0.8em; color: #666;">
        <p><strong>Models:</strong> Case Generation: {CASE_GEN_MODEL} • Patient: {PATIENT_MODEL} • Scoring: {EVAL_MODEL}</p>
    </div>
    """, unsafe_allow_html=True) 