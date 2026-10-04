import os
import streamlit as st
from dotenv import load_dotenv
from google import genai

load_dotenv()
st.set_page_config(page_title="Market & Consumer Insights Tutor", page_icon="📚", layout="centered")

SYSTEM_PROMPT = '''
You are the AI tutor for the Market and Consumer Insights course.

Use the professor's uploaded course resources as the authoritative basis for course-content answers.

Rules:
- Base substantive answers on the uploaded resources found through file search.
- Preserve the terminology and framing used in the course.
- Do not silently fill gaps with general knowledge.
- If the resources do not support an answer, say: "This is not covered in the currently available course resources."
- Never invent course rules, requirements, examples, statistics, or sources.
- Keep answers clear and concise unless the student asks for more detail.

The assignment guide is reference material only.
- You may answer factual questions about assignment requirements, structure, required analyses, recommendation standards, and submission instructions.
- Do not act as an assignment coach.
- Do not design the student's project, choose variables, write research questions, generate analysis, or complete the assignment.

Modes:
ASK: Answer directly from the resources.
EXPLAIN: Explain simply while remaining faithful to the resources.
QUIZ: Ask one question at a time using only the uploaded resources. Wait for the student's answer before evaluating it.
CHALLENGE: Ask the student to explain, compare, justify, diagnose, or apply a course concept. Ask one focused question at a time.
'''.strip()

MODE_INSTRUCTIONS = {
    "Ask the Course": "ASK mode. Answer directly from the course resources.",
    "Explain": "EXPLAIN mode. Explain simply but remain faithful to the course resources.",
    "Quiz Me": "QUIZ mode. Ask or evaluate only one question at a time using the course resources.",
    "Challenge Me": "CHALLENGE mode. Make the student reason. Ask one focused question at a time.",
}

def get_setting(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return default

def get_client():
    key = get_setting("GEMINI_API_KEY")
    if not key:
        st.error("The tutor is not configured correctly. Please contact the professor.")
        st.stop()
    return genai.Client(api_key=key)

def ask_tutor(client, store_name, mode, question):
    previous_id = st.session_state.get("previous_interaction_id")
    prompt = f"""{SYSTEM_PROMPT}

CURRENT MODE
{MODE_INSTRUCTIONS[mode]}

STUDENT MESSAGE
{question}

Use file search for substantive course-content questions.
If the resources do not support the answer, state that clearly.
""".strip()

    kwargs = dict(
        model=get_setting("GEMINI_MODEL", "gemini-3.8-flash"),
        input=prompt,
        tools=[{
            "type": "file_search",
            "file_search_store_names": [store_name],
        }],
        generation_config={"thinking_level": "low"},
    )
    if previous_id:
        kwargs["previous_interaction_id"] = previous_id

    interaction = client.interactions.create(**kwargs)
    st.session_state.previous_interaction_id = interaction.id
    return interaction

st.title("📚 Market & Consumer Insights Tutor")
st.caption("Grounded in the professor's uploaded course resources.")

store_name = get_setting("GEMINI_FILE_SEARCH_STORE")
if not store_name:
    st.error("The course knowledge base is not configured. Please contact the professor.")
    st.stop()

mode = st.radio(
    "Study mode",
    ["Ask the Course", "Explain", "Quiz Me", "Challenge Me"],
    horizontal=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "previous_interaction_id" not in st.session_state:
    st.session_state.previous_interaction_id = None

if st.button("Clear conversation"):
    st.session_state.messages = []
    st.session_state.previous_interaction_id = None
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

placeholder = {
    "Ask the Course": "Ask a question about the course...",
    "Explain": "What would you like explained?",
    "Quiz Me": "Type 'Start' or answer the current quiz question...",
    "Challenge Me": "Type a topic or 'Start'...",
}[mode]

question = st.chat_input(placeholder)

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the course resources..."):
            try:
                client = get_client()
                interaction = ask_tutor(client, store_name, mode, question)
                answer = (interaction.output_text or "").strip()
                if not answer:
                    answer = "I could not generate a response from the current course resources."
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception:
                st.error("The tutor could not answer right now. Please try again in a moment.")
