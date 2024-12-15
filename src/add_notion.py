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

    def _sanitize_keyword(self, keyword: str, max_length: int = 100) -> str:
        """キーワードを制限文字数に収める"""
        return keyword.strip()[:max_length]

    def _process_keywords(self, keywords: list) -> list:
        """キーワードリストを処理し、Notionの制限に適合させる"""
        processed_keywords = []
        for keyword in keywords:
            # 空文字列やNoneをスキップ
            if not keyword or not keyword.strip():
                continue
            
            # キーワードを制限文字数に収める
            sanitized = self._sanitize_keyword(keyword)
            if sanitized:
                processed_keywords.append(sanitized)
        
        return processed_keywords

    def _convert_markdown_to_blocks(self, text: str) -> list:
        """マークダウンテキストをNotionブロックに変換"""
        blocks = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 空行をスキップ
            if not line:
                i += 1
                continue
                
            # 見出し
            if line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"text": {"content": line[2:]}}]}
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": line[3:]}}]}
                })
            # リスト
            elif line.startswith('- ') or line.startswith('* '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"text": {"content": line[2:]}}]}
                })
            # 番号付きリスト
            elif re.match(r'^\d+\. ', line):
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [{"text": {"content": line[line.find('.')+2:]}}]}
                })
            # 通常のテキスト
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": line}}]}
                })
            
            i += 1
        
        return blocks

    def _create_notion_properties(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Notionのプロパティを生成"""
        properties = {}
        for column, config in self.config.column_configs.items():
            # タイトルとキーワードのみプロパティとして保存
            if config["notion_type"] == "multi_select":
                if column == "Keywords":
                    keywords = self._process_keywords(sections[column])
                    properties[column] = {
                        "multi_select": [{"name": k} for k in keywords]
                    }
            elif config["notion_type"] == "title":
                properties[column] = {
                    "title": [{"text": {"content": str(sections[column])}}]
                }
            # rich_text型のプロパティは作成しない

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
            
            # プロパティの作成
            properties = self._create_notion_properties(sections)
            
            # 各セクションのコンテンツをブロックに変換
            all_blocks = []
            for column, content in sections.items():
                if column != "Keywords" and column != "Name":
                    all_blocks.append({
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {"rich_text": [{"text": {"content": column}}]}
                    })
                    all_blocks.extend(self._convert_markdown_to_blocks(str(content)))
                    all_blocks.append({
                        "object": "block",
                        "type": "divider",
                        "divider": {}
                    })

            # Notionページの作成
            new_page_data = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
                "children": all_blocks
            }

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
