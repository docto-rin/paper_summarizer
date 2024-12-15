from notion_client import Client
from chat_pdf import get_summary
import config as config
import json
import re
import os
import argparse
import logging

logger = logging.getLogger(__name__)

# Notion APIキーを設定
notion = Client(auth=config.NOTION_API_KEY)

# データベースIDを設定
database_id = config.database_id

# カラム情報を設定
columns = config.columns

def add_summary2notion(pdf_path, model_name=None):
    try:
        logger.info(f"PDFの要約を開始: {pdf_path}, モデル: {model_name or 'デフォルト'}")
        plain_text = get_summary(pdf_path, model_name)
        
        if plain_text is None:
            logger.error("要約の生成に失敗しました")
            return None  # 要約生成失敗の場合はNoneを返す
            
        logger.info(f"生成された要約: {plain_text}")
        
        pattern = r'\{[^{}]+\}'
        matches = re.findall(pattern, plain_text)
        
        if not matches:
            logger.error("JSONパターンが見つかりませんでした")
            return False
            
        logger.info(f"抽出されたJSON: {matches[0]}")
        
        try:
            json_data = json.loads(matches[0])
        except json.JSONDecodeError as e:
            logger.error(f"JSONのパースに失敗: {e}")
            return False
        
        # JSONデータの前処理を追加
        for key, value in json_data.items():
            # 空の配列の場合は空文字列に変換
            if isinstance(value, list) and not value:
                json_data[key] = ""
            # 配列の場合は文字列に変換（Keywords以外）
            elif isinstance(value, list) and key != "Keywords":
                json_data[key] = ", ".join(map(str, value))

        keywords = [{"name" : keyword} for keyword in json_data['Keywords']]

        new_page_data = {
            "parent": {
                "database_id": database_id},
                "properties": {},
                "children": []
            }

        # JSONデータをキーごとにトグル形式に変換
        for key, value in json_data.items():
            toggle_block = {
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": key
                            }
                        }
                    ],
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": str(value)
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
            new_page_data["children"].append(toggle_block)


        for column in columns:
            if column == "Keywords":
                new_page_data["properties"][column] = {
                    "multi_select": keywords
                }
            elif column == "Name":
                new_page_data["properties"][column] = {
                    "title": [
                        {
                            "text": {
                                "content": str(json_data[column])  # 文字列に変換
                            }
                        }
                    ]
                }
            else:
                new_page_data["properties"][column] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": str(json_data[column])  # 文字列に変換
                            }
                        }
                    ]
                }

        try:
            response = notion.pages.create(**new_page_data)
            logger.info("Notionページの作成に成功しました")
            logger.debug(f"Notionのレスポンス: {response}")
            return True
        except Exception as e:
            logger.error(f"Notionページの作成に失敗: {e}")
            return False
            
    except Exception as e:
        logger.error(f"予期せぬエラーが発生: {e}")
        return False  # Notion追加失敗の場合はFalseを返す

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and summarize arXiv paper")
    parser.add_argument("pdf_path", nargs='?', default= "downloaded-paper.pdf", type=str, help="The pdf path want to make summarize")
    args = parser.parse_args()
    
    add_summary2notion(args.pdf_path)
