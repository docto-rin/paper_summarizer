from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from .add_notion import add_summary2notion
import os
import logging
from . import config
from .add_columns import initialize_database

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="src/templates")

# 起動時にデータベースの初期化を実行
@app.on_event("startup")
async def startup_event():
    try:
        result = initialize_database()
        if result:
            logger.info("データベースの初期化が完了しました")
        else:
            logger.info("データベースは既に初期化されています")
    except Exception as e:
        logger.error(f"データベース初期化エラー: {e}")

# papersディレクトリが存在しない場合は作成
if not os.path.exists('src/papers'):
    os.makedirs('src/papers')

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
        file_location = f"src/papers/{pdf_file.filename}"
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

# /initialize-dbエンドポイントは残しておく（APIとして利用可能）
@app.post("/initialize-db")
async def initialize_notion_db():
    try:
        result = initialize_database()
        if result:
            return {"message": "データベースのセットアップが完了しました"}
        return {"message": "データベースは既にセットアップされています"}
    except Exception as e:
        logger.error(f"データベースセットアップエラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))
