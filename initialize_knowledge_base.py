import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent
RESOURCE_DIR = BASE_DIR / "resources"
CONFIG_FILE = BASE_DIR / ".course_config.json"

FILES = [
    "01_Fundamentals_of_Market_Research.pptx",
    "02_Qualitative_Market_Research.pdf",
    "Assignment_Guide.pdf",
]

load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

store = client.file_search_stores.create(
    config={
        "display_name": "Market and Consumer Insights",
        "embedding_model": "models/gemini-embedding-2",
    }
)

for filename in FILES:
    path = RESOURCE_DIR / filename
    print("Uploading:", filename)
    operation = client.file_search_stores.upload_to_file_search_store(
        file=str(path),
        file_search_store_name=store.name,
        config={"display_name": filename},
    )
    while not operation.done:
        time.sleep(2)
        operation = client.operations.get(operation)

CONFIG_FILE.write_text(
    json.dumps({"file_search_store_name": store.name}, indent=2),
    encoding="utf-8",
)

print()
print("Ready.")
print("File Search store:", store.name)
print("Run: streamlit run app.py")
