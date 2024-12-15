import PyPDF2
import google.generativeai as genai
from . import config
import logging
import re
import json

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
    json_structure = """以下の論文を要約してJSON形式で出力してください。
出力フォーマットは必ず以下の通りとし、各項目の説明に従って内容を記述してください。
中間にMarkdown記法は使用せず、純粋なJSONのみを出力してください。

{
"""
    for column, configs in config.column_configs.items():
        if configs["notion_type"] == "multi_select":
            json_structure += f'    "{column}": [], // {configs["prompt"]}\n'
        else:
            json_structure += f'    "{column}": "", // {configs["prompt"]}\n'
    json_structure += "}"
    return json_structure

def extract_json_from_response(text):
    """応答テキストからJSONを抽出して整形する"""
    try:
        # まず { から } までの部分を抽出
        pattern = r'\{[^{}]*(?:\{[^{}]*\})*[^{}]*\}'
        matches = re.findall(pattern, text)
        if not matches:
            logger.error("JSONパターンが見つかりませんでした")
            return None
            
        # コメントを除去
        json_text = re.sub(r'//.*$', '', matches[0], flags=re.MULTILINE)
        # 末尾のカンマを除去
        json_text = re.sub(r',(\s*})', r'\1', json_text)
        
        return json.loads(json_text)
    except Exception as e:
        logger.error(f"JSON抽出処理でエラー: {e}")
        return None

def get_summary(pdf_path, model_name=None):
    pdf_text = read_pdf(pdf_path)
    prompt = create_prompt()
    
    model = get_model(model_name)
    if not model:
        return None

    try:
        response = model.generate_content(pdf_text + "\n" + prompt)
        json_data = extract_json_from_response(response.text)
        if json_data:
            return json.dumps(json_data, ensure_ascii=False)
        return None
    except Exception as e:
        logger.error(f"An error occurred with Gemini: {e}")
        return None

if __name__ == "__main__":
    print(get_summary())