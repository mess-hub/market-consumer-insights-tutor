# Market & Consumer Insights Tutor — Gemini Free-Tier Version

This version uses:

- Streamlit for the student interface
- Google Gemini API
- Gemini File Search for the course knowledge base
- the three course resources already supplied by the professor

## Important cost point

Gemini currently provides free-tier access for supported Flash models and File Search.
Free-tier limits still apply. If the class exceeds Google's free-tier rate/usage limits,
requests can be throttled or rejected.

The free tier may use submitted data to improve Google products. Do not upload confidential
student data, unpublished sensitive research, grades, or personally identifying student information.

---

# FIRST-TIME SETUP

## 1. Create a Gemini API key

Go to Google AI Studio:

https://aistudio.google.com/

Sign in with your Google account.

Choose **Get API key** and create an API key for a Google Cloud project.

Do not share the key with students.

## 2. Configure this project

Copy:

`.env.example`

and rename the copy:

`.env`

Open `.env` in Notepad and replace:

`GEMINI_API_KEY=your-gemini-api-key`

with your real Gemini API key.

Choose a professor password too:

`ADMIN_PASSWORD=your-password`

## 3. Start the app on Windows

Double-click:

`START_WINDOWS.bat`

On the first run it installs the required Python packages.

## 4. Initialize the knowledge base

In the app:

1. Choose **Professor Resources** in the sidebar.
2. Enter your professor password.
3. Click **Initialize with the 3 bundled resources**.
4. Wait while Gemini File Search uploads, chunks, and indexes them.
5. Go back to **Student Tutor**.

The initial resources are:

- Chapter 1 — Fundamentals of Market Research
- Chapter 2 — Qualitative Market Research
- Assignment Guide

---

# STUDENT MODES

## Ask the Course
Answers questions using the uploaded course resources.

## Explain
Explains course concepts more simply while remaining grounded in the resources.

## Quiz Me
Asks one question at a time and evaluates the student's response.

## Challenge Me
Makes the student explain, compare, justify, diagnose, or apply course concepts.

The assignment guide is treated only as a reference document. The tutor is instructed not to act as an assignment coach.

---

# ADDING NEW MATERIAL THROUGHOUT THE COURSE

You do not rebuild the chatbot.

Open:

**Professor Resources → Upload course resources**

Add the new PDF, PPTX, DOCX, TXT, or Markdown file and click:

**Add files to knowledge base**

The file is added to the same Gemini File Search store.

---

# FREE-TIER PRACTICAL NOTES

Google's current documentation lists File Search storage up to 1 GB for free-tier projects.
Your three course files are far below that.

File Search storage and query-time embeddings are free; free-tier model requests are also
free for supported models, subject to rate and usage limits.

Because limits can change, check the current Gemini API pricing and rate-limit pages before
rolling the tutor out to a full class.

For 100 students, test with a small group first.

---

# DEPLOYMENT

For initial testing, run it on your own computer.

To give students a public link later, deploy the folder to Streamlit Community Cloud or
another Python hosting service.

For deployment, put these in the host's secret manager rather than GitHub:

- GEMINI_API_KEY
- ADMIN_PASSWORD
- GEMINI_FILE_SEARCH_STORE

Never commit `.env` to a public repository.

---

# PROJECT FILES

- `app.py` — chatbot + professor resource manager
- `initialize_knowledge_base.py` — optional command-line initializer
- `requirements.txt`
- `.env.example`
- `START_WINDOWS.bat`
- `resources/` — the three initial course resources
