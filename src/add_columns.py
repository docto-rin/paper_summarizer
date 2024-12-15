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

# 必要な列のみを定義（database_propertyがTrueの列のみ）
required_columns = {
    name: config 
    for name, config in config.column_configs.items() 
    if config.get("database_property", False)
}

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
    column_config = config.column_configs[column_name]
    property_config = {
        column_config["notion_type"]: {}  # 空のconfigで十分
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
    """データベースを初期化し、必要な列のみを追加する"""
    existing_columns = get_database_properties(database_id)
    
    # 必要な列が全て存在するかチェック
    all_exists = all(column in existing_columns for column in required_columns)
    if all_exists:
        return False
    
    # 必要な列のみを追加
    for column_name in required_columns:
        if column_name not in existing_columns:
            add_column_to_database(database_id, column_name)
    
    return True

# メイン実行部分も簡略化
if __name__ == "__main__":
    existing_columns = get_database_properties(database_id)
    
    for column_name in required_columns:
        if column_name not in existing_columns:
            add_column_to_database(database_id, column_name)
        else:
            print(f"{column_name} カラムは既に存在します。")