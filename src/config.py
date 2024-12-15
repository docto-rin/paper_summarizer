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

# 列名とプロンプトの対応を定義
column_prompts = {
    "Name": "論文のタイトルを以下の形式で。英語原文タイトル（日本語訳）",
    "どんなもの？": "この研究は何を目的とし、どのような成果を上げたのか",
    "先行研究と比較して新規性は？": "既存研究と比較して、どのような新しい点があるのか",
    "手法のキモは？": "提案手法の核となる技術や考え方",
    "有効性はどのように検証された？": "実験や評価方法、結果の概要",
    "課題と議論は？": "研究の限界や今後の課題として挙げられている点",
    "次に読む論文等は？": "関連研究や次に読むべき論文を以下の形式で列挙して。タイトル（可能ならリンク）。レスポンスはリストやjsonではなくあくまでテキストでお願いします。",
    "Keywords": "論文の重要なキーワード（英語）",
}

# 列名のリストは、column_promptsのキーから取得
columns = list(column_prompts.keys())
