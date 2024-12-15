import PyPDF2
import google.generativeai as genai
# import openai
import config as config

# Configure Google Gemini as primary model
genai.configure(api_key=config.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# OpenAI client configuration (commented out)
# client = OpenAI(
#     api_key=config.OPENAI_API_KEY
# )

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

def get_summary(pdf_path):
    pdf_text = read_pdf(pdf_path)
    prompt = create_prompt()

    try:
        # Try with Gemini first
        response = model.generate_content(pdf_text + "\n" + prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred with Gemini: {e}")
        
        # Fallback to OpenAI (commented out)
        # try:
        #     completion = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[
        #         {"role": "system", "content": "You are a research paper summarizer."},
        #         {"role": "user", "content": pdf_text + "\n" + prompt}
        #     ]
        #     )
        #     return completion.choices[0].message.content
        # except Exception as e:
        #     print(f"An error occurred with OpenAI fallback: {e}")
        return None

if __name__ == "__main__":
    print(get_summary())