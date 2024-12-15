import requests
import json
from . import config

# NotionのAPIトークン
NOTION_API_TOKEN = config.NOTION_API_KEY

# ヘッダー情報
headers = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# データベースID
database_id = config.database_id
# 追加したいカラムのリスト
columns_to_add = config.columns

# データベースの既存カラムを取得
def get_database_properties(database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("properties", {})
    else:
        print(f"エラーが発生しました: {response.status_code}")
        print(response.text)
        return {}

# カラムを追加
def add_column_to_database(database_id, column_name):
    # Keywordsカラムの場合は特別な処理
    if column_name == "Keywords":
        property_config = {
            "multi_select": {}  # multi_selectタイプのプロパティ
        }
    else:
        property_config = {
            "rich_text": {}  # 他のカラムはrich_textタイプ
        }

    payload = {
        "properties": {
            column_name: property_config
        }
    }

    url = f"https://api.notion.com/v1/databases/{database_id}"
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print(f"{column_name} カラムが正常に追加されました。")
    else:
        print(f"{column_name} カラムの追加中にエラーが発生しました: {response.status_code}")
        print(response.text)

def initialize_database():
    """データベースを初期化し、必要なカラムを追加する"""
    existing_columns = get_database_properties(database_id)
    
    # 初期化が必要かチェック
    all_exists = all(column in existing_columns for column in columns_to_add)
    if all_exists:
        return False
    
    # カラムの追加処理
    for column in columns_to_add:
        if column not in existing_columns:
            add_column_to_database(database_id, column)
    
    return True

# 既存のカラムを取得
existing_columns = get_database_properties(database_id)

# カラムの追加処理
for column in columns_to_add:
    if column not in existing_columns:
        add_column_to_database(database_id, column)
    else:
        print(f"{column} カラムは既に存在します。")