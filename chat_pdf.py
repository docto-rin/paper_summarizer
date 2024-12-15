import PyPDF2
import google.generativeai as genai
import config as config
import logging

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

    json_structure = '""""あなたは優秀な研究者です，日本語で要約してください, KeywordsはEnglish, 以下のフォーマットでできる限り最大限具体的に，参考文献はタイトル\n{\n'
    for column in columns:
        if column == "Keywords":
            json_structure += f'    "{column}": ["", ""]\n'
        else:
            json_structure += f'    "{column}": ,\n'
    json_structure += '}"""'

    return json_structure

def get_summary(pdf_path, model_name=None):
    pdf_text = read_pdf(pdf_path)
    prompt = create_prompt()
    
    model = get_model(model_name)
    if not model:
        return None

    try:
        response = model.generate_content(pdf_text + "\n" + prompt)
        return response.text
    except Exception as e:
        logger.error(f"An error occurred with Gemini: {e}")
        return None

if __name__ == "__main__":
    print(get_summary())