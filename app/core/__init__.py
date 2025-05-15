"""
Central model registry – change here, nowhere else.
"""
CASE_GEN_MODEL      = "gpt-4o-mini"     # JSON mode ON
CASE_OUTLINE_MODEL  = "gpt-4.1-mini"      # First stage of case generation
PATIENT_MODEL       = "gpt-4.1-nano"     # free-text
SCORING_MODEL       = "gpt-4.1-mini"     # Free-text evaluator for first stage
FALLBACK_MODEL      = "gpt-4.1"          # Heavyweight rescue
EVAL_MODEL          = "gpt-4o-mini"      # JSON mode scorer for second stage
