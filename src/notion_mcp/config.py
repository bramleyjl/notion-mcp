import os
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

TASK_LIST_DB_ID = os.environ["NOTION_TASK_LIST_DB_ID"]
TASK_TEMPLATE_ID = os.environ["NOTION_TASK_TEMPLATE_ID"]

TASK_STATUSES = ["Project", "To Do", "Doing", "Done 🙌", "Blocked & Ongoing"]
