from notion_client import Client
from .chat_pdf import get_summary
import json
import re
import os
import argparse
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NotionSummaryWriter:
    def __init__(self, config_module):
        """
        NotionSummaryWriterの初期化
        Args:
            config_module: 設定モジュール（通常はsrc.config）
        """
        self.config = config_module
        self.notion = Client(auth=self.config.NOTION_API_KEY)
        self.database_id = self.config.database_id

    def _create_toggle_blocks(self, json_data: Dict[str, Any]) -> list:
        """トグルブロックを生成"""
        blocks = []
        for key, value in json_data.items():
            blocks.append({
                "object": "block",
                "type": "toggle",
                "toggle": {
                    "rich_text": [{"type": "text", "text": {"content": key}}],
                    "children": [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": str(value)}}]
                        }
                    }]
                }
            })
        return blocks

    def _create_notion_properties(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Notionのプロパティを生成"""
        properties = {}
        for column, config in self.config.column_configs.items():
            if config["notion_type"] == "multi_select":
                properties[column] = {
                    "multi_select": [{"name": keyword} for keyword in json_data[column]]
                }
            elif config["notion_type"] == "title":
                properties[column] = {
                    "title": [{"text": {"content": str(json_data[column])}}]
                }
            else:  # rich_text
                properties[column] = {
                    "rich_text": [{"text": {"content": str(json_data[column])}}]
                }
        return properties

    def add_summary(self, pdf_path: str, model_name: Optional[str] = None) -> Optional[bool]:
        """
        PDFの要約をNotionに追加
        Returns:
            None: 要約生成失敗
            True: 完全成功
            False: Notion追加失敗
        """
        try:
            logger.info(f"PDFの要約を開始: {pdf_path}, モデル: {model_name or 'デフォルト'}")
            sections = get_summary(pdf_path, model_name)
            
            if sections is None:
                logger.error("要約の生成に失敗しました")
                return None
                
            logger.info(f"生成された要約セクション: {sections.keys()}")
            
            # Notionページの作成データを準備
            new_page_data = {
                "parent": {"database_id": self.database_id},
                "properties": self._create_notion_properties(sections),
                "children": self._create_toggle_blocks(sections)
            }

            # Notionページの作成
            response = self.notion.pages.create(**new_page_data)
            logger.info("Notionページの作成に成功しました")
            logger.debug(f"Notionのレスポンス: {response}")
            return True

        except Exception as e:
            logger.error(f"予期せぬエラーが発生: {e}")
            return False

def add_summary2notion(pdf_path: str, model_name: Optional[str] = None) -> Optional[bool]:
    """レガシー互換性のための関数"""
    from . import config
    writer = NotionSummaryWriter(config)
    return writer.add_summary(pdf_path, model_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="論文要約をNotionに追加")
    parser.add_argument("pdf_path", nargs='?', default="downloaded-paper.pdf",
                       type=str, help="要約するPDFファイルのパス")
    args = parser.parse_args()
    
    from . import config  # メイン実行時のみインポート
    writer = NotionSummaryWriter(config)
    writer.add_summary(args.pdf_path)
