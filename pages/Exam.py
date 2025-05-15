import streamlit as st
import datetime
# ⛑️  guard ---------------------------------------------------------------
if "stations" not in st.session_state:    # user hit F5 or directly typed /Exam
    st.switch_page("Home.py")             # send them back to setup
# -----------------------------------------------------------------------
from app.core.timer import start, remaining
from app.core.patient import simulate
from app.core.evaluator import score
from app.core.ui import inject_css, dict_to_table, format_timer, create_station_nav
from app.core.case_generator import generate_case

# Configure page with consistent sidebar handling
st.set_page_config(
    page_title="OSCE Exam", 
    page_icon="🩺", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Get settings from session state
cfg = st.session_state.settings
station = st.session_state.stations[st.session_state.current]

# ── initialise per-station state ───────────────────────────
if "timer" not in st.session_state:
    st.session_state.timer = start(cfg["minutes"]*60)
    st.session_state.chat  = []
    st.session_state.lab   = False
    st.session_state.img   = False
    # Clear any lingering state from previous stations
    for k in ("final_answer", "early_submit", "scored"):
        if k in st.session_state:
            del st.session_state[k]

# Apply CSS (includes sidebar hiding)
inject_css()

def is_expired():
    return remaining(st.session_state.timer) == 0

# Get remaining seconds
secs = remaining(st.session_state.timer)

# Create header with improved layout
header1, header2 = st.columns([1, 4])

with header1:
    # Enhanced timer display
    format_timer(secs)
    
with header2:
    # Visual station navigation
    create_station_nav(cfg["n"], st.session_state.current)

def finish_station():
    """score this station & stash result once only"""
    if "scored" in st.session_state:
        return
    role_map = {"user": "Student", "assistant": "Patient"}
    
    # Better transcript processing with debugging
    if not st.session_state.chat:
        print("DEBUG: No chat messages found in session")
        transcript = "No conversation recorded."
    else:
        print(f"DEBUG: Processing {len(st.session_state.chat)} chat messages")
        messages = []
        for m in st.session_state.chat:
            role = role_map.get(m.get('role', ''), m.get('role', 'Unknown'))
            content = m.get('content', '')
            if content:  # Only add non-empty messages
                messages.append(f"{role}: {content}")
        
        transcript = "\n".join(messages)
        print(f"DEBUG: Generated transcript with {len(messages)} messages")
    
    cand_ans = st.session_state.get("final_answer","")
    print(f"DEBUG: Candidate diagnosis: '{cand_ans}'")
    
    # Add a loading indicator during evaluation
    with st.spinner("Evaluating your performance..."):
        st.session_state.results.append(score(transcript, cand_ans))
    
    st.session_state.scored = True
    
    # Clear flags before navigation
    for k in ("early_submit",):
        if k in st.session_state:
            del st.session_state[k]

# Progress visualization
st.progress(st.session_state.current / cfg["n"])

# Enhanced station header
st.markdown(f"""
<h2 style="margin-bottom:0;">Station {st.session_state.current+1} / {cfg['n']}</h2>
""", unsafe_allow_html=True)

# Single diagnosis input that's always visible but only enabled in the last 30 seconds
diagnosis_enabled = secs <= 30 or st.session_state.get("early_submit", False)

# Improved diagnosis input styling
if diagnosis_enabled:
    diagnosis_label = "⏱️ 30 seconds left – Enter your diagnosis:" if secs <= 30 and not st.session_state.get("early_submit", False) else "📝 Provisional diagnosis:"
    
    st.markdown('<div class="diagnosis-input">', unsafe_allow_html=True)
    st.session_state.final_answer = st.text_input(
        diagnosis_label,
        value=st.session_state.get("final_answer", ""),
        key="diagnosis_input"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ---- layout -----------------------------------------------------------
left, right = st.columns([3,2], gap="large")

with left:
    # Enhanced chief complaint display
    st.markdown(f"""
    <div style="background:#e3f2fd; border-radius:8px; padding:10px 15px; margin-bottom:15px;">
        <h3 style="margin:0; color:#0d47a1;">Chief complaint: {station.chiefComplaint}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Candidate instructions with better styling
    st.markdown('<div class="big-card">'+station.candidate_instructions+'</div>',
                unsafe_allow_html=True)

with right:
    # Enhanced patient info section
    with st.expander("🧑‍⚕️ Patient summary", expanded=True):
        p = station.patientInfo
        
        # Patient info with grid layout
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {p.name}")
            st.markdown(f"**Age:** {p.age}")
        with col2:
            st.markdown(f"**Gender:** {p.gender}")
            st.markdown(f"**Occupation:** {p.occupation}")
    
    # Combine lab and imaging requests in a dropdown
    request_option = st.selectbox(
        "Request additional information:",
        ["Select an option", "🧪 Request labs", "🖼️ Request imaging"],
        index=0
    )
    
    if request_option == "🧪 Request labs":
        st.session_state.lab = True
    elif request_option == "🖼️ Request imaging":
        st.session_state.img = True

# Display labs and imaging if requested
if st.session_state.lab:
    with st.expander("🧪 Laboratory Results", expanded=True):
        dict_to_table(station.labResults)

if st.session_state.img:
    with st.expander("🖼️ Imaging Results", expanded=True):
        dict_to_table(station.imagingResults)

# Enhanced chat interface
st.markdown("### Patient Conversation")

# Create a container for the chat history
chat_container = st.container()

with chat_container:
    # Display previous messages with enhanced styling
    for m in st.session_state.chat:
        if m["role"] == "user":
            st.markdown(f"""
            <div class="student-message">
                <strong>Student:</strong> {m["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="patient-message">
                <strong>Patient:</strong> {m["content"]}
            </div>
            """, unsafe_allow_html=True)

# Early submit button with improved styling
if not st.session_state.get("early_submit", False) and secs > 0:
    if st.button("Submit early ⏭️", use_container_width=True):
        st.session_state.early_submit = True
        st.rerun()
elif st.session_state.get("early_submit", False) and not "scored" in st.session_state:
    st.warning("Please enter your diagnosis above and confirm submission")
    if st.button("Confirm & submit", type="primary", use_container_width=True):
        # Add loading indicator during station submission
        with st.spinner("Evaluating your performance..."):
            finish_station()
        st.switch_page("pages/Results.py")

# Chat input
user_msg = st.chat_input("Ask the patient...", disabled=secs==0)
if user_msg:
    st.session_state.chat.append({"role":"user","content":user_msg})
    reply = simulate(station.model_dump(),
                     st.session_state.chat[:-1], user_msg)
    st.session_state.chat.append({"role":"assistant","content":reply})
    st.rerun()

# ----------  automatic finish on timeout  ----------
if is_expired():
    # Add loading indicator during automatic submission
    with st.spinner("Time's up! Evaluating your performance..."):
        finish_station()
    
    # Check if this was the last station
    if st.session_state.current >= cfg["n"] - 1:
        st.switch_page("pages/Results.py")
    else:
        # Move to the next station
        st.session_state.current += 1
        
        # Reset per-station state
        for k in ("timer", "chat", "lab", "img", "scored", "final_answer", "early_submit"): 
            if k in st.session_state:
                st.session_state.pop(k, None)
                
        st.rerun()

# Next station button with enhanced styling
if "scored" in st.session_state:
    if st.button("Next station ▶️", type="primary", use_container_width=True):
        # Show loading indicator for station transition
        with st.spinner("Loading next station..."):
            # reset per-station state
            for k in ("timer","chat","lab","img","scored", "final_answer", "early_submit"): 
                if k in st.session_state:
                    st.session_state.pop(k, None)
                    
            st.session_state.current += 1
            
            # Check if we need to generate a new station (in case of lazy_generation being True)
            if st.session_state.get("lazy_generation", False) and st.session_state.current >= len(st.session_state.stations) and st.session_state.current < cfg["n"]:
                with st.spinner("Generating next station..."):
                    # Get language from settings
                    language = cfg.get("language", "en")
                    st.session_state.stations.append(
                        generate_case(
                            lang=language,
                            chief_override=None,
                            settings=cfg
                        )
                    )
            
            # Check if we've completed all stations
            if st.session_state.current >= cfg["n"]:
                # Add a loading indicator for results page transition
                with st.spinner("Preparing final results..."):
                    # Ensure all stations are properly scored before moving to results
                    if len(st.session_state.results) == cfg["n"]:
                        st.switch_page("pages/Results.py")
                    else:
                        st.error(f"⚠️ Missing scores for some stations. Expected {cfg['n']} scores but got {len(st.session_state.results)}.")
                        # Give option to proceed anyway
                        if st.button("Continue to Results anyway", type="primary"):
                            st.switch_page("pages/Results.py")
            else:
                st.rerun()

# Transcript download button
if st.session_state.chat:
    st.markdown("---")
    role_map = {"user": "Student", "assistant": "Patient"}
    transcript = "\n".join(
        f"{role_map.get(m['role'], m['role'])}: {m['content']}"
        for m in st.session_state.chat
    )
    st.download_button(
        "📄 Download transcript",
        transcript,
        file_name=f"osce_station_{st.session_state.current+1}_transcript.txt",
        mime="text/plain"
    ) 