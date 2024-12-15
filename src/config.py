from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_MODEL = os.getenv('GOOGLE_MODEL', 'gemini-pro')  # デフォルト値を設定
# OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
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
        "notion_config": {}
    },
    "どんなもの？": {
        "prompt": "この研究は何を目的とし、どのような成果を上げたのか",
        "notion_type": "rich_text",
        "notion_config": {}
    },
    "新規性は？": {
        "prompt": "既存研究と比較して、どのような新しい点があるのか",
        "notion_type": "rich_text",
        "notion_config": {}
    },
    "手法のキモは？": {
        "prompt": "提案手法の核となる技術や考え方",
        "notion_type": "rich_text",
        "notion_config": {}
    },
    "検証方法は？": {
        "prompt": "実験や評価方法、結果の概要",
        "notion_type": "rich_text",
        "notion_config": {}
    },
    "課題は？": {
        "prompt": "研究の限界や今後の課題として挙げられている点",
        "notion_type": "rich_text",
        "notion_config": {}
    },
    "次に読む論文等は？": {
        "prompt": "関連研究や次に読むべき論文を以下の形式で列挙して。タイトル（可能ならリンク）。レスポンスはリストやjsonではなくあくまでテキストでお願いします。",
        "notion_type": "rich_text",
        "notion_config": {}
    },
    "Keywords": {
        "prompt": "論文の重要なキーワード（英語）",
        "notion_type": "multi_select",
        "notion_config": {}
    }
}

# 後方互換性のために既存の変数も維持
columns = list(column_configs.keys())
column_prompts = {name: config["prompt"] for name, config in column_configs.items()}
