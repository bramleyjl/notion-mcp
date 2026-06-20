import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Task List database
TASK_LIST_DB_ID = "b538833b-9b5c-450a-8bea-e60e1b83ee1f"
TASK_TEMPLATE_ID = "98373890-6458-4418-970f-74599312b9b6"

TASK_STATUSES = ["Project", "To Do", "Doing", "Done 🙌", "Blocked & Ongoing"]
