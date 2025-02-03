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
    model_name: str = Form(None),
    summary_mode: str = Form("concise"),
    pdf_mode: str = Form("text")  # デフォルトはテキストのみ
):
    try:
        # モデル名のバリデーション
        valid_models = ["gemini-1.5-pro-002", "gemini-1.5-flash-002", "gemini-2.0-flash-exp"]
        if not model_name or model_name not in valid_models:
            model_name = config.GOOGLE_MODEL
        
        logger.info(f"選択されたモデル: {model_name}")
        
        file_location = f"src/papers/{pdf_file.filename}"
        with open(file_location, "wb") as file:
            file.write(pdf_file.file.read())
        
        logger.info(f"PDFファイルを保存: {file_location}")
        
        result = add_summary2notion(file_location, model_name, summary_mode, pdf_mode)
        
        if result is None:
            output = "要約の生成に失敗しました。Geminiのエラーを確認してください。"
            status_class = "error"
            token_info = {}
            process_info = {}
        elif not result.get("success"):
            output = f"エラーが発生しました: {result.get('error', '不明なエラー')}"
            status_class = "error"
            token_info = {}
            process_info = {}
        else:
            output = "要約の生成とNotionへの追加が完了しました。"
            status_class = "success"
            token_info = result.get("token_info", {})
            process_info = result.get("process_info", {})
        
        os.remove(file_location)
        logger.info(f"一時ファイルを削除: {file_location}")
        
        total_tokens = sum(token_info.values()) if token_info else 0
        
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "output": output,
                "status_class": status_class,
                "token_count": total_tokens,
                "token_info": token_info,
                "process_info": process_info
            }
        )
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "output": f"エラーが発生しました: {str(e)}",
                "status_class": "error",
                "token_count": 0,
                "token_info": {},
                "process_info": {}
            }
        )

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
