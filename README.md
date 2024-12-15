# Paper Summarizer | 論文要約ツール

[English](#english) | [日本語](#japanese)

<a id="english"></a>
# Paper Summarizer

A tool to automatically summarize academic papers and save summaries to Notion.

## Features
- Automatic summarization of PDF papers
- Save summaries to specified Notion database
- Powered by Google Gemini Pro / Gemini 1.5 Flash
- Japanese summary output for English papers

## Setup

### 1. Get Required API Keys

#### Notion API Setup
1. Visit [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New Integration"
3. Create integration with desired name
4. Save the "Internal Integration Token"

#### Notion Database Preparation
1. Create a new database in Notion
2. Go to "..." → "Connections" in database settings
3. Add the integration you created
4. Get database ID from URL:
   ```
   https://www.notion.so/xxxxx?v=yyyy
   (xxxxx is your database ID)
   ```

#### Google API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create and save API key

### 2. Installation

```bash
# Clone repository
git clone https://github.com/docto-rin/paper_summarizer
cd paper_summarizer

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
```

### 3. Configure Environment Variables
Edit `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id
```

### 4. Run Application

```bash
uvicorn src.main:app --reload
```

Access http://127.0.0.1:8000 to start using the tool

## Usage
1. Access web interface
2. Select model (Gemini Pro or Gemini 1.5 Flash)
3. Upload PDF file
4. Click "Start Summary"
5. Results will be saved to your Notion database

## Notes
- Only supports English academic papers
- Summaries are generated in Japanese
- Ensure proper database permissions in Notion

---

<a id="japanese"></a>
# 論文要約ツール

PDFファイルをアップロードして論文を自動要約し、Notionに保存するツールです。

## 機能
- PDFファイル形式の論文を自動要約
- 要約結果をNotion上の指定データベースに自動保存
- Google Gemini Pro / Gemini 1.5 Flash による要約生成
- 英語論文を日本語で要約

## セットアップ手順

### 1. 必要なAPIキーの取得

#### Notion APIのセットアップ
1. [Notion Integrations](https://www.notion.so/my-integrations)にアクセス
2. 「New Integration」をクリック
3. 任意の名前を入力して統合を作成
4. 表示された「Internal Integration Token」を保存

#### Notionデータベースの準備
1. Notionで新しいデータベースを作成
2. データベースの右上メニューから「...」→「Connections」を選択
3. 先ほど作成した Integration を追加
4. データベースのURLからデータベースIDを取得
   ```
   https://www.notion.so/xxxxx?v=yyyy
   ※ xxxxxの部分がデータベースID
   ```

#### Google API Keyの取得
1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. APIキーを作成・保存

### 2. 環境構築

```bash
# リポジトリのクローン
git clone https://github.com/docto-rin/paper_summarizer
cd paper_summarizer

# 必要なパッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
```

### 3. 環境変数の設定
`.env`ファイルを以下のように編集:

```env
GOOGLE_API_KEY=your_google_api_key
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id
```

### 4. 起動方法

```bash
uvicorn src.main:app --reload
```

ブラウザで http://127.0.0.1:8000 にアクセスして利用開始

## 使用方法
1. Webインターフェースにアクセス
2. 使用するモデルを選択（Gemini Pro または Gemini 1.5 Flash）
3. PDFファイルをアップロード
4. 「要約を開始」をクリック
5. 処理完了後、Notionデータベースに要約結果が保存される

## 注意事項
- PDFファイルは英語論文のみ対応
- 要約結果は日本語で出力
- Notionのデータベース権限設定を確認すること