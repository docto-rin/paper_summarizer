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
        seen = set()

        for keyword in keywords:
            if not keyword:
                continue
            
            # カンマを含む場合は分割して個別のキーワードとして処理
            sub_keywords = [k.strip() for k in keyword.split(',')]
            for sub_key in sub_keywords:
                if not sub_key:
                    continue
                sanitized = self._sanitize_keyword(sub_key)
                # 重複チェックと長さ制限（Notionの制限に合わせて）
                if sanitized and sanitized.lower() not in seen and len(sanitized) <= 100:
                    processed_keywords.append(sanitized)
                    seen.add(sanitized.lower())
        
        return processed_keywords

    def _convert_markdown_to_blocks(self, text: str) -> list:
        """マークダウンテキストをNotionブロックに変換"""
        blocks = []
        lines = []
        
        # 行ごとに処理
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 1. 最も具体的な見出しから処理（最も制限が厳しいものから）
            if line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": line[4:].strip()}}]
                    }
                })
                continue
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": line[3:].strip()}}]
                    }
                })
                continue
            elif line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": line[2:].strip()}}]
                    }
                })
                continue
            
            # 2. リスト要素の処理（番号付きリストが箇条書きより制限が厳しい）
            elif line.startswith('1. '):
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"text": {"content": line[3:].strip()}}]
                    }
                })
                continue
            elif line.startswith('- ') or line.startswith('* '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": line[2:].strip()}}]
                    }
                })
                continue

            # 3. インライン要素の処理（複雑な要素から順に）
            parts = []
            current_text = ""
            i = 0
            while i < len(line):
                # ディスプレイ数式（$$）
                if line[i:i+2] == '$$':
                    if current_text:
                        parts.append({"type": "text", "content": current_text, "annotations": {}})
                    current_text = ""
                    i += 2
                    math_content = ""
                    while i < len(line) - 1 and line[i:i+2] != '$$':
                        math_content += line[i]
                        i += 1
                    if math_content:
                        parts.append({
                            "type": "equation",
                            "content": math_content
                        })
                    i += 2
                    continue
                
                # 太字かつイタリック (***)
                elif line[i:i+3] == '***':
                    if current_text:
                        parts.append({"type": "text", "content": current_text, "annotations": {}})
                    current_text = ""
                    i += 3
                    content = ""
                    while i < len(line) - 2 and line[i:i+3] != '***':
                        content += line[i]
                        i += 1
                    if content:
                        parts.append({
                            "type": "text",
                            "content": content,
                            "annotations": {"bold": True, "italic": True}
                        })
                    i += 3
                    continue
                
                # 太字 (**)
                elif line[i:i+2] == '**':
                    if current_text:
                        parts.append({"type": "text", "content": current_text, "annotations": {}})
                    current_text = ""
                    i += 2
                    content = ""
                    while i < len(line) - 1 and line[i:i+2] != '**':
                        content += line[i]
                        i += 1
                    if content:
                        parts.append({
                            "type": "text",
                            "content": content,
                            "annotations": {"bold": True}
                        })
                    i += 2
                    continue
                
                # インライン数式 ($) とイタリック (*)
                elif line[i] in ['$', '*']:
                    if current_text:
                        parts.append({"type": "text", "content": current_text, "annotations": {}})
                    current_text = ""
                    marker = line[i]
                    i += 1
                    content = ""
                    while i < len(line) and line[i] != marker:
                        content += line[i]
                        i += 1
                    if content:
                        if marker == '$':
                            parts.append({
                                "type": "equation",
                                "content": content
                            })
                        else:
                            parts.append({
                                "type": "text",
                                "content": content,
                                "annotations": {"italic": True}
                            })
                    i += 1
                    continue
                
                else:
                    current_text += line[i]
                    i += 1
            
            # 残りのテキストを追加
            if current_text:
                parts.append({"type": "text", "content": current_text, "annotations": {}})

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

    def add_summary(self, pdf_path: str, model_name: Optional[str] = None, 
                   summary_mode: str = "concise", pdf_mode: str = "text") -> Optional[Dict]:
        try:
            logger.info(f"PDFの要約を開始: {pdf_path}, モデル: {model_name or 'デフォルト'}, "
                       f"モード: {summary_mode}, PDF処理: {pdf_mode}")
            
            sections = get_summary(pdf_path, model_name, summary_mode, pdf_mode)
            if sections is None:
                return None

            # プロセス情報ブロックを作成
            token_counts = sections['_debug_info']['token_counts']
            pdf_content_tokens = token_counts.get('pdf_content', 0)
            prompt_tokens = token_counts.get('prompt', 0)
            total_input_tokens = token_counts.get('total_input', 0)

            process_info = {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"emoji": "ℹ️"},
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": f"""処理情報:
• モデル: {model_name or 'デフォルト (gemini-1.5-flash-002)'}
• 要約モード: {summary_mode}
• PDF処理モード: {pdf_mode}
• トークン使用状況:
  - PDF本文: {pdf_content_tokens:,} トークン
  - プロンプト: {prompt_tokens:,} トークン
  - 実際の入力トークン数: {total_input_tokens:,} トークン
  (注: 実際の入力トークン数はPDFとプロンプトを組み合わせた際の最終的なトークン数です)"""
                        }
                    }],
                    "color": "gray_background"
                }
            }

            # プロパティの作成を先に実行
            properties = self._create_notion_properties(sections)
            if not properties.get("Name"):  # タイトルプロパティがない場合
                properties["Name"] = {
                    "title": [{"text": {"content": "Untitled"}}]
                }

            # ブロック作成
            all_blocks = [process_info]

            all_blocks.extend([
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
            ])

            # セクションのコンテンツをブロックとして追加
            for column, content in sections.items():
                if column != "Keywords" and column != "Name" and column != "_debug_info":
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

            # プロパティの作成
            properties = self._create_notion_properties(sections)

            # メインページを作成
            try:
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
                logger.info(f"Notionページを作成: {main_page_id}")
                
                # 残りのブロックがあれば、メインページに追加
                for chunk in block_chunks[1:]:
                    self.notion.blocks.children.append(block_id=main_page_id, children=chunk)
                    logger.info(f"追加ブロックを追加: {len(chunk)} ブロック")

                return {
                    "success": True,
                    "token_info": {
                        "pdf_content": pdf_content_tokens,
                        "prompt": prompt_tokens,
                        "total_input": total_input_tokens
                    },
                    "process_info": {
                        "model": model_name or 'デフォルト',
                        "summary_mode": summary_mode,
                        "pdf_mode": pdf_mode
                    }
                }

            except Exception as notion_error:
                logger.error(f"Notionページの作成に失敗: {notion_error}")
                return {
                    "success": False,
                    "error": f"Notionページの作成に失敗: {str(notion_error)}"
                }

        except Exception as e:
            logger.error(f"予期せぬエラーが発生: {e}")
            return {
                "success": False,
                "error": str(e)
            }

def add_summary2notion(pdf_path: str, model_name: Optional[str] = None, 
                      summary_mode: str = "concise", pdf_mode: str = "text") -> Optional[Dict]:
    """レガシー互換性のための関数"""
    from . import config
    writer = NotionSummaryWriter(config)
    return writer.add_summary(pdf_path, model_name, summary_mode, pdf_mode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="論文要約をNotionに追加")
    parser.add_argument("pdf_path", nargs='?', default="downloaded-paper.pdf",
                       type=str, help="要約するPDFファイルのパス")
    args = parser.parse_args()
    
    from . import config  # メイン実行時のみインポート
    writer = NotionSummaryWriter(config)
    writer.add_summary(args.pdf_path)
