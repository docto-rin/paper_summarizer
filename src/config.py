from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_MODEL = os.getenv('GOOGLE_MODEL', 'gemini-pro')  # デフォルト値を設定
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
database_id = os.getenv('NOTION_DATABASE_ID')

# Validate environment variables
if not all([GOOGLE_API_KEY, NOTION_API_KEY, database_id]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

# 列名、プロンプト、Notionデータ型の定義
column_configs = {
    "Name": {
        "prompt": "論文のタイトルを以下の形式で。英語原文タイトル（日本語訳）",
        "notion_type": "title",
        "database_property": True  # データベースの列として追加
    },
    "どんなもの？": {
        "prompt": "この研究は何を目的とし、どのような成果を上げたのか",
        "notion_type": "rich_text",
        "database_property": False  # ページ本文としてのみ表示
    },
    "新規性は？": {
        "prompt": "既存研究と比較して、どのような新しい点があるのか",
        "notion_type": "rich_text",
        "database_property": False  # ページ本文としてのみ表示
    },
    "手法のキモは？": {
        "prompt": "提案手法の核となる技術や考え方",
        "notion_type": "rich_text",
        "database_property": False  # ページ本文としてのみ表示
    },
    "検証方法は？": {
        "prompt": "実験や評価方法、結果の概要",
        "notion_type": "rich_text",
        "database_property": False  # ページ本文としてのみ表示
    },
    "課題は？": {
        "prompt": "研究の限界や今後の課題として挙げられている点",
        "notion_type": "rich_text",
        "database_property": False  # ページ本文としてのみ表示
    },
    "次に読む論文等は？": {
        "prompt": "関連研究や次に読むべき論文を以下の形式で列挙して。タイトル（可能ならリンク）。レスポンスはリストやjsonではなくあくまでテキストでお願いします。",
        "notion_type": "rich_text",
        "database_property": False  # ページ本文としてのみ表示
    },
    "Keywords": {
        "prompt": "List 3-5 important technical keywords from the paper in English. Use commas to separate keywords. Example: deep learning, computer vision, neural networks",
        "notion_type": "multi_select",
        "database_property": True  # データベースの列として追加
    }
}

def create_prompt():
    """マークダウン形式のプロンプトを作成"""
    markdown_prompt = """Please summarize the paper in Japanese using the following format, but provide Keywords in English only.
All sections below must be included in your response, starting with '## ' for each section.
各セクションの見出しは以下の通りとし、各項目の説明に従って内容を記述してください。
※ 全てのセクションを必ず含めてください。
※ Keywordsは必ず英語で記載してください。

"""
    # ...existing code...
