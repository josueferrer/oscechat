import streamlit as st
# ⛑️  guard ---------------------------------------------------------------
if "results" not in st.session_state:    # user hit F5 or typed /Results
    st.switch_page("Home.py")            # send them back to setup
# -----------------------------------------------------------------------
import pandas as pd
import matplotlib.pyplot as plt
from app.core.ui import inject_css, dict_to_table, score_color
from app.core.checklist import CHECKLIST_ITEMS

# Configure page with consistent sidebar handling
st.set_page_config(
    page_title="OSCE Results", 
    page_icon="🩺", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply CSS (includes sidebar hiding)
inject_css()

st.title("📊 OSCE Examination Results")

if not st.session_state.results:
    st.warning("No stations were scored – did you leave before submitting?")
    st.stop()

# Calculate overall score, excluding failed stations
valid_results = [r for r in st.session_state.results if not r.get("scoring_failed", False)]
if valid_results:
    overall = sum(r["percent"] for r in valid_results) / len(valid_results)
    
    # Get color class based on score
    score_class = score_color(overall)
    
    # Enhanced overall score visualization
    st.markdown(f"""
    <div class="score-card">
        <h2>Overall Score: <span class="{score_class}">{overall:.1f}%</span></h2>
        <p>Based on {len(valid_results)} completed stations out of {len(st.session_state.stations)} total</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create score summary visualizations
    if len(valid_results) > 1:
        st.subheader("Performance across stations")
        
        # Create bar chart for station scores
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Ensure stations and scores arrays have the same length by matching up corresponding elements
        # This will fix the shape mismatch error
        stations = []
        scores = []
        for i, (s, r) in enumerate(zip(st.session_state.stations[:len(valid_results)], valid_results), 1):
            stations.append(f"Station {i}: {s.chiefComplaint[:20]}...")
            scores.append(r["percent"])
            
        # Define colors based on scores
        colors = ['#4caf50' if s >= 70 else '#ff9800' if s >= 50 else '#f44336' for s in scores]
        
        ax.bar(stations, scores, color=colors)
        ax.axhline(y=70, color='green', linestyle='--', alpha=0.5)
        ax.set_ylim(0, 100)
        ax.set_ylabel('Score (%)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        st.pyplot(fig)
        
        # Add summary table
        st.subheader("Station Summary")
        summary_data = []
        for i, (s, r) in enumerate(zip(st.session_state.stations[:len(valid_results)], valid_results), 1):
            summary_data.append({
                "Station": f"Station {i}",
                "Chief Complaint": s.chiefComplaint,
                "Score": f"{r['percent']:.1f}%",
                "Diagnosis Score": f"{r.get('diagnosis_score', 0)}/5",
                "Your Diagnosis": r.get('candidate_dx', '')
            })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
else:
    st.warning("No valid scoring data available.")
    st.header("Overall: N/A")

# Enhanced station results display
for idx, (s, r) in enumerate(zip(st.session_state.stations, st.session_state.results), 1):
    # Handle scoring failure
    if r.get("scoring_failed", False):
        st.error(f"Station {idx}: {s.chiefComplaint} — Scoring failed")
        continue
    
    # Get score color class
    station_score_class = score_color(r['percent'])
    
    # Create enhanced station header
    st.markdown(f"""
    <div style="border-left: 5px solid #{station_score_class.split('-')[-1]}; 
                padding-left: 15px; margin: 25px 0 15px 0;">
        <h3>Station {idx}: {s.chiefComplaint} — 
            <span class="{station_score_class}">{r['percent']}%</span>
        </h3>
    </div>
    """, unsafe_allow_html=True)
        
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Examiner Feedback", "Checklist", "Patient Case", "Labs & Imaging", "Download"])
    
    with tab1:
        # Formatted examiner comments
        st.markdown(f"""
        <div style="background:#f8f9fa; padding:15px; border-radius:10px; margin-bottom:20px;">
            <h4>Examiner Comments</h4>
            <p style="font-style:italic;">{r["comments"]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Diagnosis scoring with improved visualization
        diagnosis_score = r.get("diagnosis_score", 0)
        diag_score_class = score_color(diagnosis_score * 20)  # Convert 0-5 to percentage scale for color
        
        # Safely get main diagnosis
        try:
            key_dx = s.answer_key.main_diagnosis if hasattr(s.answer_key, "main_diagnosis") else "Unknown"
        except Exception:
            key_dx = "Unknown"
        
        # Create diagnosis comparison display
        st.markdown(f"""
        <div style="background:#f0f7ff; padding:15px; border-radius:10px; margin-bottom:20px;">
            <h4>Diagnosis Assessment</h4>
            <table style="width:100%;">
                <tr>
                    <td style="width:25%;"><strong>Score:</strong></td>
                    <td><span class="{diag_score_class}">{diagnosis_score}/5</span></td>
                </tr>
                <tr>
                    <td><strong>Your diagnosis:</strong></td>
                    <td>{r['candidate_dx'] or '<em>(none provided)</em>'}</td>
                </tr>
                <tr>
                    <td><strong>Correct diagnosis:</strong></td>
                    <td>{key_dx}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # Missed items with improved visualization
        st.markdown("<h4>Areas for Improvement</h4>", unsafe_allow_html=True)
        try:
            missed = [CHECKLIST_ITEMS[i] for i, v in enumerate(r["scores"]) if v == 0]
            if missed:
                st.markdown('<div style="background:#fff5f5; padding:15px; border-radius:10px;">', unsafe_allow_html=True)
                for item in missed:
                    st.markdown(f"• {item}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.success("No 0-score items – great job!")
        except Exception:
            st.warning("Could not display missed items.")

    with tab2:
        # Enhanced checklist display
        try:
            # Create dataframe with improved formatting
            df = pd.DataFrame({
                "Item": CHECKLIST_ITEMS, 
                "Score": r["scores"],
                "Feedback": r.get("item_comments", [""] * len(CHECKLIST_ITEMS))
            })
            
            # Add color-coded scores
            def color_score(val):
                if val == 5:
                    return 'background-color: #e8f5e9; color: #2e7d32'
                elif val == 3:
                    return 'background-color: #fff8e1; color: #f57c00'
                else:
                    return 'background-color: #ffebee; color: #c62828'
            
            # Apply styling using the newer .map() method instead of deprecated .applymap()
            styled_df = df.style.map(color_score, subset=['Score'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Score distribution
            score_counts = df['Score'].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(5, 3))
            ax.bar(["Not Done (0)", "Partial (3)", "Complete (5)"], 
                  [score_counts.get(0, 0), score_counts.get(3, 0), score_counts.get(5, 0)],
                  color=['#f44336', '#ff9800', '#4caf50'])
            ax.set_ylabel('Count')
            ax.set_title('Checklist Item Performance')
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"⚠️ Couldn't render full checklist: {str(e)}")

    with tab3:
        # Patient case details with improved layout
        try:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Patient info in a card
                st.markdown('<div class="score-card">', unsafe_allow_html=True)
                st.subheader("Patient Information")
                p = s.patientInfo
                st.markdown(f"**Name:** {p.name}")
                st.markdown(f"**Age:** {p.age}")
                st.markdown(f"**Gender:** {p.gender}")
                st.markdown(f"**Occupation:** {p.occupation}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Chief complaint
                st.markdown(f"#### Chief Complaint: {s.chiefComplaint}")
                
                # Patient narrative if available
                if hasattr(s, 'narrative'):
                    with st.expander("Patient Narrative", expanded=False):
                        st.write(s.narrative)
            
            with col2:
                # Medical history in a card
                st.markdown('<div class="score-card">', unsafe_allow_html=True)
                st.subheader("Medical History")
                
                # Past medical history
                if s.pastMedicalHistory:
                    for item in s.pastMedicalHistory:
                        st.markdown(f"• {item}")
                else:
                    st.markdown("*No significant past medical history*")
                
                # Medications
                st.markdown("#### Current Medications")
                if s.medications:
                    for med in s.medications:
                        st.markdown(f"• {med}")
                else:
                    st.markdown("*No medications*")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # History details in expandable section
            with st.expander("Detailed History", expanded=False):
                dict_to_table(s.historyDetails)
                
            # Diagnosis and management
            with st.expander("Diagnosis and Management", expanded=False):
                try:
                    st.markdown(f"**Main Diagnosis:** {s.answer_key.main_diagnosis}")
                    st.markdown("**Differential Diagnoses:**")
                    for dx in s.answer_key.differentials:
                        st.markdown(f"• {dx}")
                    st.markdown("**Management Plan:**")
                    for plan in s.answer_key.management:
                        st.markdown(f"• {plan}")
                except Exception:
                    st.warning("Answer key details not available")
                    
        except Exception as e:
            st.error(f"⚠️ Error displaying case details: {str(e)}")

    with tab4:
        # Lab and imaging with improved layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Laboratory Results")
            try:
                dict_to_table(s.labResults)
            except Exception:
                st.info("No lab results available.")
                
        with col2:
            st.subheader("Imaging Results")
            try:
                dict_to_table(s.imagingResults)
            except Exception:
                st.info("No imaging results available.")
    
    with tab5:
        # Download options with better UI
        try:
            st.subheader("Download Options")
            
            # Create formatted report content
            report_content = f"""OSCE Station {idx} Report
===========================================
Station: {s.chiefComplaint}
Score: {r['percent']}%

DIAGNOSIS
---------
Your diagnosis: {r['candidate_dx'] or '(none provided)'}
Correct diagnosis: {key_dx}
Diagnosis score: {diagnosis_score}/5

EXAMINER COMMENTS
----------------
{r['comments']}

CHECKLIST PERFORMANCE
-------------------
{chr(10).join([f"{item} - Score: {score}" for item, score in zip(CHECKLIST_ITEMS, r['scores'])])}
"""
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Text report download
                st.download_button(
                    "📄 Download Text Report",
                    report_content,
                    file_name=f"osce_station_{idx}_report.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # CSV download for detailed scores
                try:
                    csv_df = pd.DataFrame({
                        "Item": CHECKLIST_ITEMS,
                        "Score": r["scores"],
                        "Comments": r.get("item_comments", [""] * len(CHECKLIST_ITEMS))
                    })
                    csv = csv_df.to_csv(index=False)
                    
                    st.download_button(
                        "📊 Download CSV Scores",
                        csv,
                        file_name=f"osce_station_{idx}_scores.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                except Exception:
                    st.error("Could not generate CSV download")
                    
        except Exception:
            st.warning(f"Could not generate downloads for Station {idx}")

# Start new exam button with improved styling
st.markdown("---")
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Start New Exam 🚀", type="primary", use_container_width=True):
        st.session_state.clear()
        st.switch_page("Home.py") 