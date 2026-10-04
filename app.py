import json
import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai

APP_TITLE = "Market & Consumer Insights Tutor"
BASE_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = BASE_DIR / "resources"
CONFIG_FILE = BASE_DIR / ".course_config.json"
MANIFEST_FILE = BASE_DIR / ".resource_manifest.json"

load_dotenv(BASE_DIR / ".env")

st.set_page_config(page_title=APP_TITLE, page_icon="📚", layout="centered")

SYSTEM_PROMPT = """
You are the AI tutor for the Market and Consumer Insights course.

PURPOSE
Help students understand, review, and practice the professor's uploaded course
resources. The uploaded resources are the authoritative basis for course-content
answers.

GROUNDING RULES
1. Base substantive course answers on the uploaded course resources found through file search.
2. Preserve the terminology, framing, and level of detail used in those resources.
3. Do not silently fill gaps with general knowledge.
4. If the uploaded resources do not support an answer, say:
   "This is not covered in the currently available course resources."
5. Never invent a course rule, requirement, example, statistic, or source.
6. Keep answers clear and concise unless the student asks for more detail.
7. When the retrieved material identifies a chapter or file, mention that source naturally.

ASSIGNMENT GUIDE
The assignment guide is reference material only.
- You may answer factual questions about assignment requirements, report structure,
  required analyses, recommendation standards, and submission instructions.
- Do NOT act as an assignment coach.
- Do NOT design the student's project, choose variables, write the research question,
  generate the analysis, or complete the assignment.
- If a student asks for assignment coaching, redirect them to the relevant course
  concept or factual requirement contained in the uploaded resources.

MODES
ASK:
Answer the student's question directly from the resources.

EXPLAIN:
Explain the relevant course concept in simple language while staying faithful to
the uploaded resources.

QUIZ:
Ask one question at a time using only the uploaded course resources.
Wait for the student's answer before evaluating it.
After the student answers, briefly say what was correct and what needs improvement.

CHALLENGE:
Do not immediately provide the full answer. Ask the student to explain, compare,
justify, diagnose, or apply a concept from the course resources.
Ask one focused question at a time.
""".strip()

MODE_INSTRUCTIONS = {
    "Ask the Course": "ASK mode. Answer directly from the course resources.",
    "Explain": "EXPLAIN mode. Explain simply but remain faithful to the course resources.",
    "Quiz Me": (
        "QUIZ mode. Ask or evaluate only one question at a time using the course resources."
    ),
    "Challenge Me": (
        "CHALLENGE mode. Make the student reason. Ask one focused question at a time."
    ),
}

BUNDLED_RESOURCES = [
    "01_Fundamentals_of_Market_Research.pptx",
    "02_Qualitative_Market_Research.pdf",
    "Assignment_Guide.pdf",
]


def get_setting(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    try:
        return str(st.secrets[name])
    except Exception:
        return default


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_client():
    key = get_setting("GEMINI_API_KEY")
    if not key:
        st.error(
            "Gemini API key is not configured. Add GEMINI_API_KEY to .env "
            "or to Streamlit secrets."
        )
        st.stop()
    return genai.Client(api_key=key)


def get_store_name():
    configured = get_setting("GEMINI_FILE_SEARCH_STORE")
    if configured:
        return configured
    return load_json(CONFIG_FILE, {}).get("file_search_store_name", "")


def set_store_name(name):
    cfg = load_json(CONFIG_FILE, {})
    cfg["file_search_store_name"] = name
    save_json(CONFIG_FILE, cfg)


def manifest():
    return load_json(MANIFEST_FILE, [])


def register(filename, store_document_name=""):
    items = manifest()
    if not any(x.get("filename") == filename for x in items):
        items.append({
            "filename": filename,
            "store_document_name": store_document_name,
        })
        save_json(MANIFEST_FILE, items)


def create_store(client):
    store = client.file_search_stores.create(
        config={
            "display_name": "Market and Consumer Insights",
            "embedding_model": "models/gemini-embedding-2",
        }
    )
    set_store_name(store.name)
    return store.name


def upload_path(client, store_name, path):
    operation = client.file_search_stores.upload_to_file_search_store(
        file=str(path),
        file_search_store_name=store_name,
        config={"display_name": path.name},
    )
    while not operation.done:
        time.sleep(2)
        operation = client.operations.get(operation)
    register(path.name)
    return operation


def upload_streamlit_file(client, store_name, uploaded_file):
    tmp = BASE_DIR / f".tmp_{uploaded_file.name}"
    tmp.write_bytes(uploaded_file.getvalue())
    try:
        operation = client.file_search_stores.upload_to_file_search_store(
            file=str(tmp),
            file_search_store_name=store_name,
            config={"display_name": uploaded_file.name},
        )
        while not operation.done:
            time.sleep(2)
            operation = client.operations.get(operation)
        register(uploaded_file.name)
        return operation
    finally:
        if tmp.exists():
            tmp.unlink()


def ask_tutor(client, store_name, mode, question):
    previous_id = st.session_state.get("previous_interaction_id")
    prompt = f"""
{SYSTEM_PROMPT}

CURRENT MODE
{MODE_INSTRUCTIONS[mode]}

STUDENT MESSAGE
{question}

Use file search for substantive course-content questions. If the resources do not
support the answer, state that clearly.
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


def clear_conversation():
    st.session_state.messages = []
    st.session_state.previous_interaction_id = None


def student_view():
    st.title("📚 Market & Consumer Insights Tutor")
    st.caption("Grounded in the professor's uploaded course resources.")

    store_name = get_store_name()
    if not store_name:
        st.warning(
            "The course knowledge base has not been initialized yet. "
            "The professor needs to open Professor Resources first."
        )
        return

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
        clear_conversation()
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
    if not question:
        return

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
            except Exception as exc:
                st.error(f"Could not generate an answer: {exc}")


def professor_view():
    st.title("🔐 Professor Resources")
    st.caption("Add course materials to the same knowledge base throughout the semester.")

    admin_password = get_setting("ADMIN_PASSWORD")
    if admin_password:
        entered = st.text_input("Professor password", type="password")
        if entered != admin_password:
            st.info("Enter the professor password to continue.")
            return
    else:
        st.warning(
            "ADMIN_PASSWORD is not configured. Set one before sharing the app with students."
        )

    client = get_client()
    store_name = get_store_name()

    st.subheader("1. Course knowledge base")
    if store_name:
        st.success("Knowledge base is initialized.")
        st.code(store_name)
    else:
        if st.button("Initialize with the 3 bundled resources", type="primary"):
            try:
                with st.spinner("Creating the File Search store and indexing the resources..."):
                    store_name = create_store(client)
                    for filename in BUNDLED_RESOURCES:
                        path = RESOURCE_DIR / filename
                        if path.exists():
                            upload_path(client, store_name, path)
                st.success("Knowledge base created and the three resources were added.")
                st.rerun()
            except Exception as exc:
                st.error(f"Initialization failed: {exc}")
                return

    if not store_name:
        return

    st.subheader("2. Add new resources")
    new_files = st.file_uploader(
        "Upload course resources",
        type=["pdf", "pptx", "docx", "txt", "md"],
        accept_multiple_files=True,
    )
    if new_files and st.button("Add files to knowledge base"):
        successes, failures = [], []
        with st.spinner("Uploading and indexing..."):
            for item in new_files:
                try:
                    upload_streamlit_file(client, store_name, item)
                    successes.append(item.name)
                except Exception as exc:
                    failures.append(f"{item.name}: {exc}")
        if successes:
            st.success("Added: " + "; ".join(successes))
        if failures:
            st.error("Could not add: " + "; ".join(failures))

    st.subheader("3. Resource register")
    items = manifest()
    if items:
        for item in items:
            st.write(f"• {item['filename']}")
    else:
        st.caption("No local resource register yet.")

    st.divider()
    st.caption(
        "The assignment guide is a reference source only. "
        "The tutor is instructed not to act as an assignment coach."
    )


page = st.sidebar.radio("View", ["Student Tutor", "Professor Resources"])
st.sidebar.caption("Add new resources during the semester without rebuilding the app.")

if page == "Student Tutor":
    student_view()
else:
    professor_view()
