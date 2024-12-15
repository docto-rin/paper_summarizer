from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from add_notion import add_summary2notion
import subprocess
import os
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# papersディレクトリが存在しない場合は作成
if not os.path.exists('./papers'):
    os.makedirs('./papers')

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/get-paper", response_class=HTMLResponse)
async def get_paper(request: Request, paper_id: str = Form(...)):
    try:
        logger.info(f"arXiv ID: {paper_id}の処理を開始")
        result = subprocess.run(
            ["python3", "get_paper_by_id.py", paper_id],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        output = result.stdout.strip()
        logger.info(f"処理結果: {output}")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        output = f"エラーが発生しました: {str(e)}"
    
    return templates.TemplateResponse("result.html", {"request": request, "output": output})

@app.post("/upload-pdf", response_class=HTMLResponse)
async def upload_pdf(request: Request, pdf_file: UploadFile = File(...)):
    try:
        file_location = f"./papers/{pdf_file.filename}"
        with open(file_location, "wb") as file:
            file.write(pdf_file.file.read())
        
        logger.info(f"PDFファイルを保存: {file_location}")
        
        # 直接add_summary2notionを呼び出す
        result = add_summary2notion(file_location)
        logger.info(f"Notionへの追加結果: {result}")
        
        if result:
            output = "要約の生成とNotionへの追加が完了しました。"
        else:
            output = "要約の生成は完了しましたが、Notionへの追加に失敗した可能性があります。"
        
        os.remove(file_location)
        logger.info(f"一時ファイルを削除: {file_location}")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        output = f"エラーが発生しました: {str(e)}"
    
    return templates.TemplateResponse("result.html", {"request": request, "output": output})
