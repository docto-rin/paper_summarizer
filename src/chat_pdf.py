import PyPDF2
import google.generativeai as genai
from . import config
import logging
import re
from typing import Union, Any

logger = logging.getLogger(__name__)

# Configure Google Gemini
genai.configure(api_key=config.GOOGLE_API_KEY)

def get_model(model_name=None):
    """モデルのインスタンスを取得"""
    model_name = model_name or config.GOOGLE_MODEL
    try:
        return genai.GenerativeModel(model_name=model_name)
    except Exception as e:
        logger.error(f"モデルの初期化に失敗: {e}")
        return None

def get_pdf_content(pdf_path: str, mode: str = "text") -> Union[str, Any]:
    """
    PDFの内容を取得（モードに応じて処理方法を変更）
    
    Args:
        pdf_path: PDFファイルのパス
        mode: 処理モード ("text" or "full")
    
    Returns:
        str: テキストモードの場合は抽出されたテキスト
        Any: PDF全体モードの場合はGemini File APIのアップロード結果
    """
    if mode == "text":
        # テキストのみモード
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text()
        return text
    else:
        # PDF全体モード
        return genai.upload_file(pdf_path)

def read_pdf(file_path):
    """PDFファイルからテキストを抽出（レガシー）"""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

def create_prompt(sections_to_generate=None, is_title_only=False):
    """マークダウン形式のプロンプトを作成"""
    if is_title_only:
        return """Extract the paper title and translate it to Japanese.
Output in the following format only, nothing else:

## Name
[Original English Title] ([Japanese Translation])

Example:
## Name
Attention Is All You Need (注意機構がすべて)

Rules:
1. Keep the original English title exactly as written in the paper
2. Japanese translation should be in parentheses
3. Do not include any other information
4. Do not include paper authors, dates, or other metadata
5. Must start with '## Name'
"""
    
    markdown_prompt = """Please summarize the paper in Japanese using the following format...
"""
    configs_to_use = (
        {name: cfg for name, cfg in config.column_configs.items() if name in sections_to_generate}
        if sections_to_generate
        else config.column_configs
    )
    
    for column, configs in configs_to_use.items():
        markdown_prompt += f"## {column}\n{configs['prompt']}\n\n"
    return markdown_prompt

def extract_sections_from_markdown(text, needed_sections=None):
    """マークダウンテキストから各セクションを抽出"""
    sections = {}
    current_section = None
    current_content = []
    
    for line in text.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
                current_content = []
            current_section = line[3:].strip()
        elif current_section:
            current_content.append(line)
    
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    # 必要なセクションのみを確認
    if needed_sections:
        missing_sections = set(needed_sections) - set(sections.keys())
        if missing_sections:
            logger.warning(f"以下のセクションが見つかりません: {missing_sections}")
            return sections  # エラーにはせず、取得できたセクションを返す
    
    # Keywords を配列に変換し、整形
    if 'Keywords' in sections:
        keywords = [k.strip() for k in re.split(r'\s*[,;]\s*', sections['Keywords'])]
        sections['Keywords'] = [k for k in keywords if k]
    
    return sections

def get_summary(pdf_path, model_name=None, summary_mode="concise", pdf_mode="text"):
    model = get_model(model_name)
    if not model:
        return None

    try:
        pdf_content = get_pdf_content(pdf_path, pdf_mode)
        sections = {}
        
        # トークンカウント用のヘルパー関数を追加
        def count_input_tokens(content_list):
            count_response = model.count_tokens(content_list)
            # CountTokensResponseオブジェクトから整数値を取得
            return count_response.total_tokens

        # まずタイトルだけを取得（最大5回試行）
        for attempt in range(5):
            try:
                title_prompt = create_prompt(sections_to_generate=["Name"], is_title_only=True)
                # トークン数をカウント
                title_tokens = count_input_tokens([pdf_content, title_prompt])
                logger.info(f"Title generation input tokens: {title_tokens}")
                
                # トークン数をカウント
                token_count = model.count_tokens([pdf_content, title_prompt])
                logger.info(f"Title generation input tokens: {token_count}")
                
                title_response = model.generate_content([pdf_content, title_prompt])
                title_sections = extract_sections_from_markdown(title_response.text, needed_sections=["Name"])
                
                if title_sections and "Name" in title_sections:
                    sections.update(title_sections)
                    logger.info("タイトルの取得に成功しました")
                    break
                    
                logger.warning(f"タイトルの取得に失敗 (試行 {attempt + 1}/5)")
            except Exception as e:
                logger.warning(f"タイトル生成エラー (試行 {attempt + 1}/5): {e}")
        
        if "Name" not in sections:
            logger.error("論文タイトルの取得に失敗しました")
            return None

        # 必要なセクションを特定（タイトルを除く）
        needed_sections = {
            name for name, cfg in config.column_configs.items()
            if (summary_mode == "detailed" or cfg.get("required", False)) and name != "Name"
        }

        # メインの要約を取得
        main_prompt = create_prompt(needed_sections)
        # トークン数をカウント
        main_tokens = count_input_tokens([pdf_content, main_prompt])
        logger.info(f"Main content generation input tokens: {main_tokens}")
        
        main_response = model.generate_content([pdf_content, main_prompt])
        main_sections = extract_sections_from_markdown(main_response.text, needed_sections)
        
        if main_sections:
            sections.update(main_sections)

        # 不足しているセクションを特定
        missing_sections = needed_sections - set(sections.keys())

        # 不足しているセクションがある場合、個別に再試行
        if missing_sections:
            logger.info(f"再取得を試みるセクション: {missing_sections}")
            for missing_section in missing_sections:
                if config.column_configs[missing_section].get("required", False):
                    # 必須セクションは3回まで試行
                    max_attempts = 3
                else:
                    # オプショナルセクションは1回のみ試行
                    max_attempts = 1
                    
                for attempt in range(max_attempts):
                    try:
                        section_prompt = create_prompt([missing_section])
                        response = model.generate_content([pdf_content, section_prompt])
                        section_result = extract_sections_from_markdown(
                            response.text, 
                            needed_sections=[missing_section]
                        )
                        
                        if section_result and missing_section in section_result:
                            sections[missing_section] = section_result[missing_section]
                            logger.info(f"セクション {missing_section} の再取得に成功")
                            break
                        else:
                            logger.warning(f"セクション {missing_section} の再取得に失敗 (試行 {attempt + 1}/{max_attempts})")
                    except Exception as e:
                        logger.warning(f"セクション {missing_section} の生成エラー (試行 {attempt + 1}/{max_attempts}): {e}")

        # トークン数情報を追加
        sections['_debug_info'] = {
            'token_counts': {
                'title': title_tokens,
                'main_content': main_tokens
            }
        }

        # 必須セクションが揃っているか最終確認
        final_missing = {
            name for name in needed_sections | {"Name"}
            if name not in sections and config.column_configs[name].get("required", False)
        }
        
        if final_missing:
            logger.error(f"以下の必須セクションの取得に失敗: {final_missing}")
            return None

        return sections

    except Exception as e:
        logger.error(f"An error occurred with Gemini: {e}")
        return None

if __name__ == "__main__":
    print(get_summary())