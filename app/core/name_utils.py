import random

# English names
MALE_EN   = ["Michael Carter", "Robert Johnson", "David Lee",
          "Anthony Green", "Steven Rogers", "Carlos Ramirez"]
FEMALE_EN = ["Maria Gonzales", "Patricia Adams", "Jennifer Brown",
          "Linda Cooper", "Barbara Stewart", "Natalie Wood"]

# Arabic/Gulf names
MALE_AR   = ["Mohammed Al-Mansouri", "Ahmed Al-Hashimi", "Abdullah Al-Qahtani",
          "Khalid Al-Subai", "Youssef Al-Farsi", "Omar Al-Shamsi"]
FEMALE_AR = ["Fatima Al-Marri", "Aisha Al-Suwaidi", "Noura Al-Qasimi",
          "Maryam Al-Bloushi", "Hessa Al-Falasi", "Latifa Al-Maktoum"]

def generate_name(gender:str, lang:str="en") -> str:
    """Generate a culturally appropriate name based on gender and language"""
    if lang == "ar":
        bank = MALE_AR if gender.lower().startswith("m") else FEMALE_AR
    else:
        bank = MALE_EN if gender.lower().startswith("m") else FEMALE_EN
    return random.choice(bank) 