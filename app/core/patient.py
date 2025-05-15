from textwrap import dedent
import json
import random
from typing import List, Dict
from app.core.llm import chat
from app.core import PATIENT_MODEL, EVAL_MODEL

# Emotional and behavioral variations for fallback
EMOTIONS = ["worried", "anxious", "irritated", "relieved", "tearful", "stoical", "confused", "concerned"]
PERSONALITY_TRAITS = ["reserved", "chatty", "curious", "analytical", "dramatic", "humorous", "sarcastic"]
COPING_STYLES = ["stoical", "denial", "humor", "anger", "bargaining", "spiritual"]

def initialize_patient_state(case: dict) -> dict:
    """Create a persistent state for the patient that won't change during the session"""
    return {
        "repeat_questions": set(),  # track repeated questions
        "question_count": 0,
        "greeting_done": False,
        "context_generated": False  # Whether we've generated rich context yet
    }

def generate_personal_context(case: dict) -> dict:
    """Generate a simple personal context for the patient - lightweight version"""
    info = case["patientInfo"]
    chief_complaint = case.get("chiefComplaint", "health concerns")
    
    # Check if the case already has personality traits - use those if available
    if hasattr(case, 'personality') and hasattr(case.personality, 'trait'):
        traits = [case.personality.trait]
        coping = case.personality.coping_style if hasattr(case.personality, 'coping_style') else random.choice(COPING_STYLES)
        backstory = case.backstory if hasattr(case, 'backstory') and case.backstory else ""
    else:
        # Generate basic traits if not available in the case
        traits = random.sample(PERSONALITY_TRAITS, 2)
        coping = random.choice(COPING_STYLES)
        backstory = ""
    
    return {
        "personality_traits": traits,
        "coping_style": coping,
        "backstory": backstory,
        "key_concerns": [chief_complaint]
    }

def post_process_response(response: str) -> str:
    """Ensure response is properly formatted and not cut off"""
    # Split into sentences
    sentences = []
    for s in response.split('.'):
        if s.strip():
            sentences.append(s.strip() + '.')
    
    # Take up to 3 sentences
    sentences = sentences[:3]
    
    # If response seems to be cut off (ends without punctuation), add ellipsis
    result = " ".join(sentences)
    if result and not result[-1] in '.!?':
        result += "..."
        
    return result

def make_json_serializable(obj):
    """Convert non-serializable types to serializable ones"""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, set):
        return list(obj)  # Convert set to list
    else:
        return obj

def simulate(case:dict, history:list, user_msg:str) -> str:
    info = case["patientInfo"]
    
    # Create or retrieve patient state
    if "patient_state" not in case:
        case["patient_state"] = initialize_patient_state(case)
    
    patient_state = case["patient_state"]
    
    # Generate context if not already done
    if not patient_state.get("context_generated", False):
        patient_state["context"] = generate_personal_context(case)
        patient_state["context_generated"] = True
    
    # Get context info
    context = patient_state["context"]
    traits = ", ".join(context.get("personality_traits", ["concerned"]))
    
    # Track repeats and questions
    is_repeat = user_msg.lower().strip() in patient_state["repeat_questions"]
    patient_state["repeat_questions"].add(user_msg.lower().strip())
    patient_state["question_count"] += 1
    
    # First interaction flag
    is_first_turn = not patient_state.get("greeting_done", False) and patient_state["question_count"] == 1
    if is_first_turn:
        patient_state["greeting_done"] = True
    
    # Detect language from the case or settings
    language = "en"  # Default to English
    if "lang" in case:
        language = case["lang"]
    elif "settings" in case and "language" in case["settings"]:
        language = case["settings"]["language"]
    
    # Language-specific instruction
    language_instruction = ""
    if language == "ar":
        language_instruction = """
IMPORTANT: RESPOND IN ARABIC. All your replies must be in Arabic (العربية).
Use appropriate Arabic expressions, cultural references, and conversational style."""
    
    # Create a streamlined system prompt that's still rich but more efficient
    system_prompt = f"""You're a patient named {info['name']} (age {info['age']}, {info['occupation']}).

KEY FACTS:
- Chief complaint: {case.get("chiefComplaint", "health concerns")}
- Personality: {traits}
- Coping style: {context.get("coping_style", "stoical")}
{f'- Backstory: {context.get("backstory", "")}' if context.get("backstory") else ''}
{language_instruction}

HOW TO RESPOND:
- Be authentic and natural - a real person, not a medical textbook
- Keep responses brief (1-3 sentences)
- If the same question repeats, show slight frustration
- First question? Mention why you're seeking medical help
- Include emotions and reactions where appropriate"""
    
    # Create serializable case with medical details (but trimmed down)
    serializable_case = make_json_serializable({
        "chiefComplaint": case.get("chiefComplaint", ""),
        "historyDetails": case.get("historyDetails", {}),
        "pastMedicalHistory": case.get("pastMedicalHistory", []),
        "medications": case.get("medications", [])
    })
    
    # Complete system content
    sys_content = system_prompt + f"\n\n# MEDICAL DETAILS (reference only):\n{json.dumps(serializable_case, indent=2)}"

    messages = [{"role": "system", "content": sys_content}] + history + [{"role":"user", "content": user_msg}]

    # Use PATIENT_MODEL (gpt-4.1-mini) with higher max_tokens
    response = chat(messages, model=PATIENT_MODEL, temperature=0.7, max_tokens=300)
    
    # Post-process to fix any issues
    return post_process_response(response) 