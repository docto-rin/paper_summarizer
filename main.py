from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from add_notion import add_summary2notion
import os
import logging
import config

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
    return templates.TemplateResponse("index.html", {
        "request": request,
        "default_model": config.GOOGLE_MODEL
    })

@app.post("/upload-pdf", response_class=HTMLResponse)
async def upload_pdf(
    request: Request,
    pdf_file: UploadFile = File(...),
    model_name: str = Form(None)
):
    try:
        file_location = f"./papers/{pdf_file.filename}"
        with open(file_location, "wb") as file:
            file.write(pdf_file.file.read())
        
        logger.info(f"PDFファイルを保存: {file_location}")
        
        # モデル名を指定して要約を実行
        result = add_summary2notion(file_location, model_name)
        logger.info(f"Notionへの追加結果: {result}")
        
        if result is None:  # 要約生成失敗
            output = "要約の生成に失敗しました。Geminiのエラーを確認してください。"
        elif result is True:  # 完全に成功
            output = "要約の生成とNotionへの追加が完了しました。"
        else:  # Notionへの追加失敗
            output = "要約の生成は完了しましたが、Notionへの追加に失敗しました。"
        
        os.remove(file_location)
        logger.info(f"一時ファイルを削除: {file_location}")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        output = f"エラーが発生しました: {str(e)}"
    
    return templates.TemplateResponse("result.html", {"request": request, "output": output})
