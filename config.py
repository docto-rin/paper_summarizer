from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
database_id = os.getenv('NOTION_DATABASE_ID')

# Validate environment variables
if not all([GOOGLE_API_KEY, NOTION_API_KEY, database_id]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

columns = [
    "Name",
    "どんなもの？",
    "先行研究と比較して新規性は？",
    "手法のキモは？",
    "有効性はどのように検証された？",
    "課題と議論は？",
    "次に読む論文等は？",
    "Keywords"
]
