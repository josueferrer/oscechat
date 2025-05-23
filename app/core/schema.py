"""
FULL schema for an OSCE case.  Every OpenAI response MUST validate here.
"""
from pydantic import BaseModel, Field
from typing import List, Dict

class PatientInfo(BaseModel):
    name: str
    age: int
    gender: str
    occupation: str
    
    model_config = {"extra": "forbid"}

class Personality(BaseModel):
    trait: str  # chatty, terse, irritable, anxious, optimistic
    coping_style: str  # jokes, denial, stoical
    
    model_config = {"extra": "forbid"}

class AnswerKey(BaseModel):
    main_diagnosis: str
    differentials: List[str]
    management: List[str]
    
    model_config = {"extra": "forbid"}

class OsceCase(BaseModel):
    narrative: str                          # 60-100-word prose summary
    candidate_instructions: str
    marking_sheet: List[str]                      # 35 items
    patientInfo: PatientInfo
    chiefComplaint: str
    historyDetails: Dict
    pastMedicalHistory: List[str]
    familyHistory: List[str]
    medications: List[str]
    socialHistory: Dict
    reviewOfSystems: Dict
    physicalFindings: List[str]
    labResults: Dict
    imagingResults: Dict
    keyHistoryQuestions: List[str]
    keyExamManeuvers: List[str]
    answer_key: AnswerKey                        # Strongly typed answer key
    personality: Personality = Field(default_factory=lambda: Personality(trait="chatty", coping_style="stoical"))
    backstory: str = ""                # 80-100 words about family, work, stressors
    lang: str = "en"                  # Language code (en, ar) for patient responses
    
    model_config = {"extra": "forbid", "validate_assignment": True}

# This object is **sent from the UI to the evaluator**, not generated by GPT
class CandidateAnswer(BaseModel):
    main_diagnosis: str = ""
    differentials: List[str] = []
    management: List[str] = []
    
    model_config = {"extra": "forbid"} 