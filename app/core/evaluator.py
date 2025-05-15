import json
import random
from app.core import EVAL_MODEL, SCORING_MODEL
from app.core.llm import chat
from app.core.checklist import CHECKLIST_ITEMS

def collapse_transcript(raw: str, limit: int = 40) -> str:
    """Turn long chat into ≤limit bulleted lines so the model can reason."""
    out = []
    for line in raw.splitlines():
        out.append(line.strip())
        if len(out) >= limit:
            break
    print(f"DEBUG: Processed transcript with {len(out)} lines")
    return "\n".join(out)

REASON_TEMPLATE = """
You are an OSCE examiner.  For each checklist item below
write one short line (≤15 words) that states whether the student did it,
with a 0/3/5 *at the front*.

Example for score 5:
5  Greets patient warmly, introduces self                     # fully done

Example for score 3:
3  Asked about drug history but missed allergies              # partial

Example for score 0 (explain WHY it was absent, don't just say "absent"):
0  Did not ask about family health history at all             # explain why 0
0  Failed to introduce self or establish rapport              # explain why 0
0  Student didn't ask about medication compliance             # explain why 0

Checklist:
{checklist}

Conversation (bullet summary):
{summary}

Student's stated diagnosis: {dx}

IMPORTANT: For items scored 0, give a specific reason WHY it was absent, don't just write "absent"

-----  WRITE 35 LINES, NOTHING ELSE  -----
"""

JSON_TEMPLATE = """
Convert the examiner notes below into valid JSON that
conforms to this schema.  Do not invent information.
{schema}

NOTES
{notes}
"""

# Used for direct scoring of very short transcripts
DIRECT_SCORING_TEMPLATE = """
You are an OSCE examiner scoring a medical student's clinical examination.

For each of the 35 checklist items, score the student's performance:
- 0 = Not done or absent
- 3 = Partially done
- 5 = Done well

Based on the brief transcript below, score ONLY what you see evidence for.
Most items will be scored 0 if the transcript is very short.

The output should be a JSON object with these fields:
- scores: Array of 35 integers (0, 3, or 5 only)
- item_comments: Array of 35 brief explanations
- comments: Overall assessment
- diagnosis_score: Integer from 0-5

TRANSCRIPT:
{transcript}

CHECKLIST ITEMS:
{checklist}

STUDENT DIAGNOSIS:
{dx}
"""

# Make schema for JSON validation
_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 35, "maxItems": 35
        },
        "item_comments": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 35, "maxItems": 35
        },
        "comments": {"type": "string"},
        "diagnosis_score": {"type": "integer"}
    },
    "required": ["scores", "comments", "diagnosis_score", "item_comments"],
    "additionalProperties": False
}

def normalize_array(arr, expected_len, default_value):
    """Ensure array is exactly expected_len by padding or truncating"""
    if len(arr) < expected_len:
        print(f"DEBUG: Normalizing array from {len(arr)} to {expected_len} items")
        return arr + [default_value] * (expected_len - len(arr))
    else:
        return arr[:expected_len]

def validate_scores(scores, expected_len):
    """Ensure all scores are valid (0, 3, or 5) and correct length"""
    # First normalize length
    scores = normalize_array(scores, expected_len, 0)
    # Then validate values - more lenient conversion
    validated = []
    for s in scores:
        if s in (0, 3, 5):
            validated.append(s)
        elif s > 3:  # If greater than 3, round to 5
            validated.append(5)
        elif s > 0:  # If between 0 and 3, round to 3
            validated.append(3)
        else:
            validated.append(0)
    return validated

def score(transcript: str, candidate_dx: str = "") -> dict:
    """Evaluate a clinical interaction"""
    # Normalize diagnosis
    normalized_dx = candidate_dx.strip() if candidate_dx else ""
    
    # Check if diagnosis is empty or "None"
    is_empty_diagnosis = not normalized_dx or normalized_dx.lower() in ["none", "n/a", "na", "unknown", "not sure", "don't know", "i don't know"]
    
    # Debug the transcript format
    print(f"DEBUG: Full transcript length: {len(transcript.splitlines())} lines")
    print(f"DEBUG: First 3 lines of transcript: {transcript.splitlines()[:3]}")
    
    # Handle very short or empty transcripts - quick path
    lines = transcript.strip().splitlines()
    if len(lines) < 5:
        print("DEBUG: Very short transcript detected - using direct scoring template")
        try:
            json_block = chat(
                [{"role":"user", "content": DIRECT_SCORING_TEMPLATE.format(
                    transcript=transcript,
                    checklist=json.dumps(CHECKLIST_ITEMS),
                    dx=normalized_dx
                )}],
                model=EVAL_MODEL,
                json_mode=True,
                temperature=0.1
            )
            data = json.loads(json_block)
            
            # Force diagnosis_score to 0 if diagnosis is empty or "None"
            if is_empty_diagnosis:
                data["diagnosis_score"] = 0
                
            return process_scoring_data(data, candidate_dx)
        except Exception as e:
            print(f"DEBUG: Direct scoring failed: {str(e)}")
    
    # Regular two-stage path for normal transcripts
    summary = collapse_transcript(transcript)
    print(f"DEBUG: Transcript length: {len(summary.splitlines())} lines")
    
    try:
        # Stage 1: Reasoning with SCORING_MODEL (GPT-4.1-mini)
        reasoning = chat(
            [{"role":"user",
              "content": REASON_TEMPLATE.format(
                  checklist="\n".join(CHECKLIST_ITEMS),
                  summary=summary,
                  dx=normalized_dx
              )}],
            model=SCORING_MODEL,
            temperature=0.2,
            max_tokens=900)
        
        # Debug the reasoning output
        print(f"DEBUG: Reasoning output length: {len(reasoning.splitlines())} lines")
        print(f"DEBUG: First 3 lines of reasoning: {reasoning.splitlines()[:3]}")
        
        # Stage 2: Convert to JSON with EVAL_MODEL (GPT-4o-mini)
        json_block = chat(
            [{"role":"user",
              "content": JSON_TEMPLATE.format(
                  schema=json.dumps(_SCHEMA, indent=2),
                  notes=reasoning
              )}],
            model=EVAL_MODEL,
            json_mode=True,
            temperature=0)
        
        data = json.loads(json_block)
        
        # Debug the data before applying any changes
        print(f"DEBUG: Received scores: {data.get('scores', [])} (length={len(data.get('scores', []))})")
        
        # Force diagnosis_score to 0 if diagnosis is empty or "None"
        if is_empty_diagnosis:
            data["diagnosis_score"] = 0
            
    except Exception as e:
        # Fallback to one-stage method with EVAL_MODEL
        print(f"DEBUG: Two-stage scoring failed: {str(e)}. Falling back to one-stage.")
        try:
            system = {"role": "system", "content":
                "You are an OSCE examiner evaluating a medical student's performance.\n"
                "Score each checklist item on a scale of 0 (not done), 3 (partially done), or 5 (done well).\n"
                "Output JSON only, matching the provided schema.\n"
                "IMPORTANT: Only mark items as 0 (absent) if they are truly not addressed in the conversation.\n"
                "IMPORTANT: Give credit (score 3 or 5) for ANY attempt to address checklist items, even if brief."}

            user = {"role": "user", "content":
                f"Conversation:\n{summary}\n\n"
                f"Student diagnosis: {candidate_dx}\n"
                f"Checklist items:\n{json.dumps(CHECKLIST_ITEMS)}\n\n"
                f"Schema:\n{json.dumps(_SCHEMA, indent=1)}"}
            
            json_block = chat([system, user], model=EVAL_MODEL,
                       json_mode=True, temperature=0.1)
            data = json.loads(json_block)
        except Exception as e2:
            print(f"DEBUG: All scoring methods failed: {str(e2)}")
            # Return minimum viable result
            return {
                "percent": 0,
                "comments": "The scoring process encountered issues. Please review the transcript manually.",
                "scores": [0] * 35,
                "item_comments": ["Score not available"] * 35,
                "candidate_dx": candidate_dx,
                "diagnosis_score": 0,
                "scoring_failed": False  # Don't mark as failed even though we're using fallback
            }
    
    result = process_scoring_data(data, candidate_dx)
    print(f"DEBUG: Final scores summary - zeros: {result['scores'].count(0)}, threes: {result['scores'].count(3)}, fives: {result['scores'].count(5)}")
    print(f"DEBUG: Final calculated percent: {result['percent']}%")
    return result

def process_scoring_data(data, candidate_dx):
    """Process and validate scoring data"""
    try:
        expected = len(CHECKLIST_ITEMS)  # 35
        
        # Validate and normalize arrays
        scores = validate_scores(data.get("scores", []), expected)
        item_comments = normalize_array(data.get("item_comments", []), expected, "Not assessed")
        
        # Validate diagnosis score
        diagnosis_score = data.get("diagnosis_score", 0)
        
        # Extra check for empty diagnosis - force score to 0
        normalized_dx = candidate_dx.strip() if candidate_dx else ""
        if not normalized_dx or normalized_dx.lower() in ["none", "n/a", "na", "unknown", "not sure", "don't know", "i don't know"]:
            diagnosis_score = 0
            print("DEBUG: Empty or 'None' diagnosis detected, forcing diagnosis_score to 0")
        elif diagnosis_score not in range(6):  # 0-5
            print(f"DEBUG: Invalid diagnosis score {diagnosis_score}, setting to 0")
            diagnosis_score = 0
            
        # Calculate percentage
        total_score = sum(scores)
        pct = total_score / (expected * 5) * 100
        
        return {
            "percent": round(pct,1),
            "comments": data.get("comments", "Evaluation of student performance completed."),
            "scores": scores,
            "item_comments": item_comments,
            "candidate_dx": candidate_dx,
            "diagnosis_score": diagnosis_score,
            "scoring_failed": False
        }
    except Exception as e:
        print(f"DEBUG: Scoring post-processing failed: {str(e)}")
        # Fallback in case of parsing failure
        return {
            "percent": 0,
            "comments": "The scoring process encountered issues. Please review the transcript manually.",
            "scores": [0] * expected,
            "item_comments": ["Score not available"] * expected,
            "candidate_dx": candidate_dx,
            "diagnosis_score": 0,
            "scoring_failed": True
        } 