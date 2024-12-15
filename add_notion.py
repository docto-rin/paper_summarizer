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

def add_summary2notion(pdf_path):
    try:
        logger.info(f"PDFの要約を開始: {pdf_path}")
        plain_text = get_summary(pdf_path)
        
        if plain_text == None:
            logger.error("要約の生成に失敗しました")
            return False
            
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
                                "content": json_data[column]
                            }
                        }
                    ]
                }
            else:
                new_page_data["properties"][column] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": json_data[column]
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
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and summarize arXiv paper")
    parser.add_argument("pdf_path", nargs='?', default= "downloaded-paper.pdf", type=str, help="The pdf path want to make summarize")
    args = parser.parse_args()
    
    add_summary2notion(args.pdf_path)
