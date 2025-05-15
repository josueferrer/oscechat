# OSCE Chat Simulator

A medical training application that simulates patient encounters for medical students, implementing the Objective Structured Clinical Examination (OSCE) format.

## Features

- Timed clinical stations with countdown timer
- AI-powered patient simulation
- Clinical cases with detailed parameters
- Hints available for guidance
- Mandatory final diagnosis entry
- Detailed performance feedback and scoring
- Multilingual support (English and Arabic)

## Requirements

- Python 3.9+
- OpenAI API key

## Local Setup

1. Clone this repository:
```bash
git clone https://github.com/josueferrer/oscechat.git
cd oscechat
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
streamlit run Home.py
```

## Deployment on Streamlit Cloud

1. Fork this repository
2. Create a new app on [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Add your OpenAI API key as a secret:
   - Name: `OPENAI_API_KEY`
   - Value: `your_api_key_here`
5. Deploy the app

## License

MIT 