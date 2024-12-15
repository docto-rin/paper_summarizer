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
        """
        キーワードを制限文字数に収め、表記を統一する
        - 先頭文字を大文字に
        - 複合語の場合は各単語の先頭文字を大文字に
        """
        # 基本的なクリーニング
        cleaned = keyword.strip()
        
        # 複合語を考慮して各単語の先頭を大文字に
        # 例: "deep learning" → "Deep Learning"
        # 例: "natural language processing" → "Natural Language Processing"
        words = cleaned.split()
        capitalized = ' '.join(word.capitalize() for word in words)
        
        return capitalized[:max_length]

    def _process_keywords(self, keywords: list) -> list:
        """キーワードリストを処理し、Notionの制限に適合させる"""
        processed_keywords = []
        seen = set()  # 重複チェック用

        for keyword in keywords:
            if not keyword:
                continue
            
            sanitized = self._sanitize_keyword(keyword)
            if sanitized and sanitized.lower() not in seen:
                processed_keywords.append(sanitized)
                seen.add(sanitized.lower())
        
        return processed_keywords

    def _convert_markdown_to_blocks(self, text: str) -> list:
        """マークダウンテキストをNotionブロックに変換"""
        blocks = []
        lines = []
        current_math = []
        in_display_math = False
        in_inline_math = False
        
        # 行ごとに処理
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # ディスプレイ数式の処理
            if '$$' in line:
                # ...existing code for display math...
                continue

            # ディスプレイ数式の内容を収集
            if in_display_math:
                current_math.append(line)
                continue

            # インライン装飾とインライン数式を処理
            parts = []
            current_text = ""
            i = 0
            while i < len(line):
                # ディスプレイ数式のチェック
                if line[i:i+2] == '$$':
                    i += 2
                    continue
                
                # 太字 (***) の処理
                elif line[i:i+3] == '***':
                    if current_text:
                        parts.append({"type": "text", "content": current_text, "annotations": {}})
                    current_text = ""
                    i += 3
                    bold_italic_content = ""
                    while i < len(line) - 2 and line[i:i+3] != '***':
                        bold_italic_content += line[i]
                        i += 1
                    if bold_italic_content:
                        parts.append({
                            "type": "text",
                            "content": bold_italic_content,
                            "annotations": {"bold": True, "italic": True}
                        })
                    i += 3
                    continue
                
                # 太字 (**) の処理
                elif line[i:i+2] == '**':
                    if current_text:
                        parts.append({"type": "text", "content": current_text, "annotations": {}})
                    current_text = ""
                    i += 2
                    bold_content = ""
                    while i < len(line) - 1 and line[i:i+2] != '**':
                        bold_content += line[i]
                        i += 1
                    if bold_content:
                        parts.append({
                            "type": "text",
                            "content": bold_content,
                            "annotations": {"bold": True}
                        })
                    i += 2
                    continue
                
                # イタリック (*) の処理
                elif line[i] == '*':
                    if current_text:
                        parts.append({"type": "text", "content": current_text, "annotations": {}})
                    current_text = ""
                    i += 1
                    italic_content = ""
                    while i < len(line) and line[i] != '*':
                        italic_content += line[i]
                        i += 1
                    if italic_content:
                        parts.append({
                            "type": "text",
                            "content": italic_content,
                            "annotations": {"italic": True}
                        })
                    i += 1
                    continue
                
                # インライン数式 ($) の処理
                elif line[i] == '$':
                    if current_text:
                        parts.append({"type": "text", "content": current_text, "annotations": {}})
                    current_text = ""
                    i += 1
                    math_content = ""
                    while i < len(line) and line[i] != '$':
                        math_content += line[i]
                        i += 1
                    if math_content:
                        parts.append({
                            "type": "equation",
                            "content": math_content
                        })
                    i += 1
                    continue

                else:
                    current_text += line[i]
                    i += 1
            
            # 残りのテキストを追加
            if current_text:
                parts.append({"type": "text", "content": current_text, "annotations": {}})

            # 通常のマークダウン要素の処理
            if line.startswith('# '):
                # ...existing heading and list processing code...
                continue

            # パーツから段落ブロックを作成
            if parts:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": part["content"]},
                                "annotations": part.get("annotations", {})
                            } if part["type"] == "text" else {
                                "type": "equation",
                                "equation": {"expression": part["content"]}
                            }
                            for part in parts
                        ]
                    }
                })

        # 未完了の数式ブロックを処理
        if current_math:
            blocks.append({
                "object": "block",
                "type": "equation",
                "equation": {
                    "expression": '\n'.join(current_math)
                }
            })

        return blocks

    def _create_notion_properties(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Notionのプロパティを生成"""
        properties = {}
        for column, config in self.config.column_configs.items():
            if not config.get("database_property", False):
                continue
                
            if column not in sections:
                logger.warning(f"セクション {column} が見つかりません")
                continue

            if config["notion_type"] == "multi_select":
                # Keywordsの処理
                if (column == "Keywords"):
                    keywords = self._process_keywords(sections[column])
                    properties[column] = {
                        "multi_select": [{"name": k} for k in keywords]
                    }
            elif config["notion_type"] == "title":
                # タイトルの処理
                properties[column] = {
                    "title": [{"text": {"content": str(sections[column])}}]
                }
            else:  # rich_text
                # その他のデータベースプロパティとして表示する項目
                properties[column] = {
                    "rich_text": [{"text": {"content": str(sections[column])}}]
                }

        return properties

    def _create_subpage_blocks(self, title: str, blocks: list) -> dict:
        """サブページを作成するためのデータを生成"""
        return {
            "object": "block",
            "type": "child_page",
            "child_page": {
                "title": title
            },
            "children": blocks
        }

    def add_summary(self, pdf_path: str, model_name: Optional[str] = None, summary_mode: str = "concise") -> Optional[bool]:
        """
        PDFの要約をNotionに追加
        Returns:
            None: 要約生成失敗
            True: 完全成功
            False: Notion追加失敗
        """
        try:
            logger.info(f"PDFの要約を開始: {pdf_path}, モデル: {model_name or 'デフォルト'}, モード: {summary_mode}")
            sections = get_summary(pdf_path, model_name, summary_mode)
            
            if sections is None:
                logger.error("要約の生成に失敗しました")
                return None
            
            # プロパティの作成（database_property: Trueの項目はデータベースにも表示）
            properties = self._create_notion_properties(sections)
            
            # ブロックを作成（目次から始める）
            all_blocks = [
                {
                    "object": "block",
                    "type": "table_of_contents",
                    "table_of_contents": {}
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                }
            ]
            
            # 各セクションのコンテンツをブロックとして追加
            for column, content in sections.items():
                if column != "Keywords" and column != "Name":
                    all_blocks.extend([
                        {
                            "object": "block",
                            "type": "heading_2",
                            "heading_2": {"rich_text": [{"text": {"content": column}}]}
                        },
                        *self._convert_markdown_to_blocks(str(content)),
                        {
                            "object": "block",
                            "type": "divider",
                            "divider": {}
                        }
                    ])

            # 100ブロックごとに分割して保存
            MAX_BLOCKS = 90  # 余裕を持って90に設定
            block_chunks = [all_blocks[i:i + MAX_BLOCKS] for i in range(0, len(all_blocks), MAX_BLOCKS)]
            
            # メインページを作成
            main_page = {
                "parent": {"database_id": self.database_id},
                "properties": properties,
                "children": block_chunks[0] if block_chunks else []
            }
            
            main_response = self.notion.pages.create(**main_page)
            main_page_id = main_response["id"]
            
            # 残りのブロックがあれば、メインページに追加
            for chunk in block_chunks[1:]:
                self.notion.blocks.children.append(block_id=main_page_id, children=chunk)

            logger.info("Notionページの作成に成功しました")
            return True

        except Exception as e:
            logger.error(f"予期せぬエラーが発生: {e}")
            return False

def add_summary2notion(pdf_path: str, model_name: Optional[str] = None, summary_mode: str = "concise") -> Optional[bool]:
    """レガシー互換性のための関数"""
    from . import config
    writer = NotionSummaryWriter(config)
    return writer.add_summary(pdf_path, model_name, summary_mode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="論文要約をNotionに追加")
    parser.add_argument("pdf_path", nargs='?', default="downloaded-paper.pdf",
                       type=str, help="要約するPDFファイルのパス")
    args = parser.parse_args()
    
    from . import config  # メイン実行時のみインポート
    writer = NotionSummaryWriter(config)
    writer.add_summary(args.pdf_path)
