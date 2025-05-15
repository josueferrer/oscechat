import streamlit as st
import pandas as pd

CSS = """
<style>
/* Hide sidebar completely */
[data-testid="collapsedControl"] {display: none;}
section[data-testid="stSidebar"] {display: none;}
.main .block-container {padding-top: 2rem;}

/* Base components */
.big-card {
    background: #f5f7fa;
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.lab-table th {
    text-align: left !important;
    padding: 8px;
    border-bottom: 1px solid #eee;
}
.lab-table td {
    padding: 8px;
    border-bottom: 1px solid #eee;
}

/* Enhanced timer styles */
.timer-normal {
    background: #e7f5f9;
    border-radius: 20px;
    padding: 8px 16px;
    display: inline-block;
    margin-bottom: 10px;
    font-weight: 600;
}
.timer-warning {
    background: #fff3cd;
    border-radius: 20px;
    padding: 8px 16px;
    display: inline-block;
    margin-bottom: 10px;
    font-weight: 600;
    animation: pulse 1s infinite;
}
.timer-danger {
    background: #f8d7da;
    border-radius: 20px;
    padding: 8px 16px;
    display: inline-block;
    margin-bottom: 10px;
    font-weight: 600;
    animation: pulse 0.5s infinite;
}
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

/* Chat message styling */
.patient-message {
    background: #f0f7ff;
    border-radius: 12px;
    padding: 10px 15px;
    margin-bottom: 8px;
    position: relative;
}
.student-message {
    background: #f1f3f5;
    border-radius: 12px;
    padding: 10px 15px;
    margin-bottom: 8px;
    position: relative;
}

/* Diagnosis input */
.diagnosis-input {
    background: #fff9db;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #ffe066;
    margin-top: 10px;
}

/* Results page styles */
.score-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
.score-high {
    color: #2e7d32;
    font-weight: bold;
}
.score-medium {
    color: #ff9800;
    font-weight: bold;
}
.score-low {
    color: #d32f2f;
    font-weight: bold;
}

/* Station navigation */
.station-nav {
    display: flex;
    gap: 8px;
    margin-bottom: 15px;
    flex-wrap: wrap;
}
.station-indicator {
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: #e0e0e0;
    font-weight: bold;
    font-size: 14px;
}
.station-current {
    background: #1976d2;
    color: white;
}
.station-completed {
    background: #4caf50;
    color: white;
}

/* Feature list styling */
.feature-list {
    margin: 20px 0;
}
.feature-item {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}
.feature-icon {
    margin-right: 10px;
    font-size: 1.2em;
}

/* Info box styling */
.info-box {
    background-color: #e6f3ff;
    padding: 15px;
    border-radius: 5px;
    margin: 20px 0;
    border-left: 4px solid #1976d2;
}
</style>
"""

def inject_css():
    """Apply all CSS styling to the app"""
    st.markdown(CSS, unsafe_allow_html=True)

def dict_to_table(d: dict):
    """Display a dictionary as a styled table"""
    if not d:  # Handle empty dict case
        return st.info("No data available")
    
    # Convert any complex values (lists, dicts) to strings to ensure compatibility with Arrow
    processed_values = {}
    for key, value in d.items():
        if isinstance(value, (list, dict)):
            processed_values[key] = str(value)
        else:
            processed_values[key] = value
    
    df = pd.DataFrame({"Test": processed_values.keys(), "Result": processed_values.values()})
    st.table(df.style.set_table_attributes('class="lab-table"'))

def create_station_nav(total_stations, current_station):
    """Create a visual station navigation indicator"""
    html = '<div class="station-nav">'
    for i in range(total_stations):
        if i < current_station:
            cls = "station-indicator station-completed"
        elif i == current_station:
            cls = "station-indicator station-current"
        else:
            cls = "station-indicator"
        html += f'<div class="{cls}">{i+1}</div>'
    html += '</div>'
    return st.markdown(html, unsafe_allow_html=True)

def format_timer(seconds):
    """Format and display the timer with appropriate styling"""
    minutes, secs = divmod(seconds, 60)
    
    timer_class = "timer-normal"
    if seconds <= 30:
        timer_class = "timer-warning"
    if seconds <= 10:
        timer_class = "timer-danger"
        
    html = f"""
    <div class="{timer_class}">
        <span>⏰ {minutes}:{secs:02d}</span>
    </div>
    """
    return st.markdown(html, unsafe_allow_html=True)

def score_color(score):
    """Return appropriate color class based on score"""
    if score >= 70:
        return "score-high"
    elif score >= 50:
        return "score-medium"
    else:
        return "score-low"

def feature_list(features):
    """Display a stylized feature list with icons"""
    # Create HTML for each feature with proper spacing and formatting
    items_html = ""
    for icon, text in features:
        items_html += f'<div class="feature-item"><span class="feature-icon">{icon}</span><span>{text}</span></div>\n'
    
    # Wrap in container div and apply proper styling
    html = f"""
    <div class="feature-list">
    {items_html}
    </div>
    """
    
    # Use st.markdown with unsafe_allow_html=True to render the HTML
    st.markdown(html, unsafe_allow_html=True)

def info_box(text, icon="ℹ️"):
    """Display an informational box with an icon"""
    # Create clean, properly formatted HTML
    html = f"""
    <div class="info-box">
        <p><span style="font-size:1.2em;margin-right:8px;">{icon}</span>{text}</p>
    </div>
    """
    
    # Render the HTML
    st.markdown(html, unsafe_allow_html=True) 