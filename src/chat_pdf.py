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

columns = config.columns

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
    markdown_prompt = """以下の論文を要約してマークダウン形式で出力してください。
各セクションの見出しは以下の通りとし、各項目の説明に従って内容を記述してください。

"""
    for column, configs in config.column_configs.items():
        markdown_prompt += f"## {column}\n{configs['prompt']}\n\n"
    return markdown_prompt

def extract_sections_from_markdown(text):
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
    
    # Keywords を配列に変換
    if 'Keywords' in sections:
        sections['Keywords'] = [k.strip() for k in sections['Keywords'].split(',')]
    
    return sections

def get_summary(pdf_path, model_name=None):
    pdf_text = read_pdf(pdf_path)
    prompt = create_prompt()
    
    model = get_model(model_name)
    if not model:
        return None

    try:
        response = model.generate_content(pdf_text + "\n" + prompt)
        sections = extract_sections_from_markdown(response.text)
        if sections:
            return sections
        return None
    except Exception as e:
        logger.error(f"An error occurred with Gemini: {e}")
        return None

if __name__ == "__main__":
    print(get_summary())