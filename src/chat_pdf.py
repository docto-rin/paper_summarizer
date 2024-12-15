import PyPDF2
import google.generativeai as genai
from . import config
import logging
import re

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

def read_pdf(file_path):
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text

def create_prompt():
    """マークダウン形式のプロンプトを作成"""
    markdown_prompt = """Please summarize the paper in Japanese using the following format, but provide Keywords in English only.
各セクションの見出しは以下の通りとし、各項目の説明に従って内容を記述してください。
※ Keywordsは必ず英語で記載してください。

"""
    for column, configs in config.column_configs.items():
        markdown_prompt += f"## {column}\n{configs['prompt']}\n\n"
    return markdown_prompt

def extract_sections_from_markdown(text):
    """マークダウンテキストから各セクションを抽出"""
    sections = {}
    current_section = None
    current_content = []
    required_sections = set(config.column_configs.keys())  # 必要なセクションを記録
    
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
    
    # 必要なセクションが全て存在するか確認
    missing_sections = required_sections - set(sections.keys())
    if missing_sections:
        logger.error(f"必要なセクションが見つかりません: {missing_sections}")
        return None
    
    # Keywords を配列に変換し、整形
    if 'Keywords' in sections:
        # 主な区切り文字（カンマ、セミコロン）でのみ分割
        keywords = [k.strip() for k in re.split(r'\s*[,;]\s*', sections['Keywords'])]
        # 空でない要素のみを保持
        sections['Keywords'] = [k for k in keywords if k]
    
    return sections

def get_summary(pdf_path, model_name=None):
    pdf_text = read_pdf(pdf_path)
    prompt = create_prompt()
    
    model = get_model(model_name)
    if not model:
        return None

    try:
        # 最大3回まで再試行
        for attempt in range(3):
            try:
                response = model.generate_content(pdf_text + "\n" + prompt)
                sections = extract_sections_from_markdown(response.text)
                if sections:
                    return sections
                logger.warning(f"応答の解析に失敗 (試行 {attempt + 1}/3)")
            except Exception as e:
                logger.warning(f"要約生成エラー (試行 {attempt + 1}/3): {e}")
        
        logger.error("全ての試行が失敗しました")
        return None
        
    except Exception as e:
        logger.error(f"An error occurred with Gemini: {e}")
        return None

if __name__ == "__main__":
    print(get_summary())