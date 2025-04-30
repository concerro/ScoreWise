# ScoreLift - AI Credit Analysis App

A premium, AI-powered credit report analyzer that delivers actionable, step-by-step advice and a downloadable PDF report. Designed for both beginners and professionals.

---

## Features
- **Modern, beautiful UI** (glassmorphism, responsive, TailwindCSS)
- **AI-powered analysis** using OpenAI GPT-4o Structured Outputs
- **Personalized, actionable advice** (executive summary, step-by-step plan, 90-day roadmap, FAQ)
- **Downloadable PDF report** (no system dependencies required)
- **Privacy-first**: Your data is never stored

---

## Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/llSourcell/credit_analyzer.git
cd credit_analyzer
```

### 2. Set up your Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure your OpenAI API Key
- Copy `.env.example` to `.env` (or create a `.env` file)
- Add your OpenAI API key:
  ```env
  OPENAI_API_KEY=your_openai_api_key_here
  ```

### 4. Run the app
```bash
source venv/bin/activate
python app.py
```
- The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000)

### 5. Using the App
- **Step 1:** Upload a PDF credit report (from Experian, Equifax, or TransUnion)
- **Step 2:** View your premium, actionable analysis
- **Step 3:** Download your personalized PDF report

---

## Troubleshooting
- **Missing dependencies?** Run `pip install -r requirements.txt` again.
- **OpenAI errors?** Double-check your API key in `.env`.
- **PDF not downloading?** Ensure you’re running the latest code and refresh the page.

---

## Tech Stack
- Python (Flask)
- OpenAI GPT-4o
- WeasyPrint (for PDF generation)
- TailwindCSS

---

## License
MIT

---

## Credits
Built by @llSourcell and contributors. Feel free to fork and improve!
# ScoreLift
