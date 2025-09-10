# mod-diary 📝✨

AI × 感情分析 × 可視化の日記アプリ  
日々の出来事や気分をスライダーで記録すると、AIが感情を解析してグラフやカレンダーで振り返ることができます。

---

## 🚀 主な機能
- 📖 日記投稿（テキスト＋画像添付）
- 😊 ムードスライダー（0〜10段階）＋絵文字表示
- 🤖 感情分析（BERT 日本語モデル）
- 📅 カレンダー表示（FullCalendar）
- 📊 統計グラフ（Chart.js 折れ線・円・棒グラフ）
- 🐾 相棒キャラクターのランダムな挨拶

---

## 🛠 技術スタック
- **Backend**: Flask (Python)
- **DB**: SQLite（開発用）
- **Frontend**: HTML / CSS / JavaScript
- **AI**: HuggingFace Transformers (日本語感情分析モデル)
- **Storage**: Google Cloud Storage (GCS)  
  ※ローカル開発時は `static/uploads` に保存も可能

---

## 📂 ディレクトリ構成
mod-diary/
├── app.py              # メインアプリ
├── templates/          # HTMLテンプレート
├── static/             # 静的ファイル（CSS/JS/画像）
├── data/               # SQLite DB（初回起動時に自動生成）
└── model/              # メッセージ生成・翻訳モジュール

---

## ⚙️ セットアップ方法

### 1. 環境を準備
```bash
git clone https://github.com/<yourname>/mod-diary.git
cd mod-diary
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

----
### 2. 環境変数を設定
export FLASK_APP=app.py
export SECRET_KEY=your-secret-key
export GCS_BUCKET=your-bucket-name
# GCSを使う場合のみ
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

### 3. 起動

flask run

http://127.0.0.1:5000 にアクセス！

📊 初期データについて
	•	data/diary.db は .gitignore に含まれています。
	•	初回起動時に init_db() により自動で生成されます。

⸻

🌱 今後のアイデア
	•	AI Bot / モバイル連携
	•	10年日記機能
	•	写真＋AI自動タグ付け
	•	感情の長期トレンド分析

📜 ライセンス

MIT License
