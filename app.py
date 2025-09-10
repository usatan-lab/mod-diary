from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os, json
from datetime import datetime
from transformers import pipeline
import os
import random
from werkzeug.utils import secure_filename
from google.cloud import storage
from PIL import Image
import imghdr
import uuid
from datetime import timedelta
# ────────────────────────────────────────────────
#  プロジェクト内モジュール
# ────────────────────────────────────────────────
from model.message_generator import generate_message
from model.translator import translate_emotion

# ────────────────────────────────────────────────
#  キャラクター定義
# ────────────────────────────────────────────────
# CHAR_SLUG = {"ネコ": "neko", "イヌ": "inu", "ウサギ": "usagi"}
ALL_CHARS = [
    {"name": "ネコ", "img": "images/neko.png"},
    {"name": "イヌ", "img": "images/inu.png"},
    {"name": "ウサギ", "img": "images/usagi.png"},
]
CHAR_IMG_MAP = {c["name"]: c["img"] for c in ALL_CHARS}

# ────────────────────────────────────────────────
#  初期設定
# ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data", "diary.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTS = {"jpg","jpeg","png","gif","webp"}


app.secret_key = "change‑me"
app.config.update(
    SESSION_COOKIE_SECURE=True,      # httpsのみ
    SESSION_COOKIE_HTTPONLY=True,    # JSから不可
    SESSION_COOKIE_SAMESITE="Lax",
)

# 単一ソース
CATEGORIES = [
    ("日常・ライフログ", "☕️"),
    ("趣味・推し活",     "🫶"),
    ("家族・育児",       "🧺"),
    ("ポジティブログ",   "🌈"),
    ("パートナー・恋愛", "🤍"),
]


MOOD_LEVEL_LABELS = {
  0:"Very Sad",1:"Sad",2:"Upset",3:"Anxious",4:"Tired",
  5:"Neutral",6:"Grateful",7:"Content",8:"Happy",9:"Very Happy",10:"Euphoric"
}
EMOJI_MAP = {0:"😭",1:"😢",2:"😣",3:"😟",4:"😮‍💨",5:"😐",6:"🙏",7:"🙂",8:"😄",9:"🤩",10:"🥳"}

MOOD_TAGS = {
    "楽しい": 8,
    "悲しい": 2,
    "怒り": 3,
    "不安": 3,
    "幸せ": 9,
    "疲労": 4,
    "感謝": 6,
    "感動": 8,
}

# ────────────────────────────────────────────────
#  GCS 関連
# ────────────────────────────────────────────────
# GCS_BUCKET = os.getenv("GCS_BUCKET")
# storage_client = storage.Client()
# bucket = storage_client.bucket(GCS_BUCKET)

# def _is_image(file_stream):
#     # 1) 実体チェック（Pillowで開けるか）
#     try:
#         img = Image.open(file_stream)
#         img.verify()
#         file_stream.seek(0)
#     except Exception:
#         return False
#     # 2) 署名偽装対策（imghdrでざっくり）
#     kind = imghdr.what(file_stream)
#     file_stream.seek(0)
#     return kind in {"jpeg","png","gif","webp"}

# def upload_image_to_gcs(file_storage, prefix="uploads/"):
#     # 拡張子・MIMEの軽チェック
#     filename = file_storage.filename or ""
#     ext = filename.rsplit(".",1)[-1].lower() if "." in filename else ""
#     if ext not in ALLOWED_EXTS:
#         raise ValueError("許可されていない拡張子です。")

#     # 実体が画像か判定
#     if not _is_image(file_storage.stream):
#         raise ValueError("画像として不正です。")
#     file_storage.stream.seek(0)

#     # ランダム名（推測防止）
#     safe_name = f"{prefix}{uuid.uuid4().hex}.{ext}"
#     blob = bucket.blob(safe_name)

#     # 非公開アップロード（推奨）
#     blob.cache_control = "public, max-age=31536000"  # 公開する場合は有効。非公開でも問題なし
#     blob.upload_from_file(file_storage.stream, content_type=file_storage.mimetype)

#     return safe_name  # GCS上のパス（gs:// ではなくオブジェクト名）

@app.context_processor
def inject_mood_maps():
    return dict(MOOD_LEVEL_LABELS=MOOD_LEVEL_LABELS, EMOJI_MAP=EMOJI_MAP)

@app.template_filter('mood_label')
def mood_label_filter(lvl):
    try: return MOOD_LEVEL_LABELS[int(lvl)]
    except: return 'Unknown'

MAIN_CATEGORIES     = [name for name, _ in CATEGORIES]
MAIN_CATEGORY_ICONS = dict(CATEGORIES)
DEFAULT_ICON = "📓"

def cat_icon(name: str) -> str:
    return MAIN_CATEGORY_ICONS.get(name, DEFAULT_ICON)


def clamp_mood(level):
    try:
        level = int(level)
    except (TypeError, ValueError):
        level = 5
    return max(0, min(10, level))

def sign_url_for_view(object_name, minutes=60):
    blob = bucket.blob(object_name)
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=minutes),
        method="GET",
    )
    return url

# ────────────────────────────────────────────────
#  アップロード関連
# ────────────────────────────────────────────────

# ───── 拡張子セット ─────
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# ────────────────────

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#  ────────────────────────────────────────────────
#  ホーム画面の挨拶
# ────────────────────────────────────────────────

GREETINGS = [
    "おかえり！",
    "今日も来てくれてうれしいな！",
    "待ってたよ！",
    "お疲れさま！",
    "やったー！また会えたね！"  
]

#  ────────────────────────────────────────────────
#  感情分析ユーティリティ
# ────────────────────────────────────────────────

def analyze_sentiment(text: str):
    """BERT でテキストを感情分類 → (label, auto_comment) を返す"""
    try:
        model_id = "alter-wang/bert-base-japanese-emotion-lily"
        classifier = pipeline("sentiment-analysis", model=model_id, tokenizer=model_id)
        result = classifier(text)[0] 
        label = result["label"]
        comments = {
            "joy": "楽しそうだね！✨",
            "trust": "いい時間だったのかな？",
            "fear": "ちょっと不安だった？💭",
            "surprise": "びっくりしたことがあったんだね！😲",
            "sadness": "つらかったね…😢",
            "disgust": "イヤな気分になっちゃったのかも…💦",
            "anger": "むかっときた感じ…？💢",
            "anticipation": "何か楽しみにしてるのかな？😌",
        }
        return label, comments.get(label, "日記を書いてくれてありがとう！")
    except Exception as e:
        print("感情分析エラー:", e)
        return "neutral", "日記を書いてくれてありがとう！"

# ────────────────────────────────────────────────
#  DB 初期化
# ────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS diary(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content       TEXT NOT NULL,
                sentiment     TEXT,
                mood_tag      TEXT,
                main_category TEXT,
                created_at    TEXT
            )"""
    )
    c.execute("PRAGMA table_info(diary)")
    cols = {row[1] for row in c.fetchall()}

    if "mood_level" not in cols:
        c.execute("ALTER TABLE diary ADD COLUMN mood_level INTEGER")
    if "image_path" not in cols:
        c.execute("ALTER TABLE diary ADD COLUMN image_path TEXT")

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def index():
    # --- キャラクター関連 ---
    chosen     = session.get("characters", ["ネコ"])
    main_char  = chosen[0]
    char_img   = CHAR_IMG_MAP[main_char]
    greeting   = random.choice(GREETINGS)

    # --- 日記一覧を取得 ---
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT id, content, mood_tag, main_category, created_at
              FROM diary
          ORDER BY created_at DESC
        """)
        diaries = c.fetchall()

    # --- まとめてテンプレートへ ---
    return render_template(
        "index.html",
        char_img   = char_img,
        main_char  = main_char,
        characters = chosen,        # = session.get("characters", …)
        greeting   = greeting,
        diaries    = diaries
    )

@app.route("/characters", methods=["GET", "POST"])
def character_select():
    if request.method == 'POST':
        session["characters"] = request.form.getlist('characters')[:3]
        return redirect(url_for("index"))
    return render_template("character_select.html", all_chars=ALL_CHARS)

@app.route('/new_diary', methods=['GET', 'POST'])
def new_diary():
    if request.method == 'POST':
        content = (request.form.get('content') or '').strip()
        main_category = request.form.get('main_category') or request.form.get('genre') or "日常・ライフログ"

        # 0–10 のムード（未対応テンプレでも安全に）
        if 'mood_level' in request.form:
            mood_level = clamp_mood(request.form.get('mood_level'))
            mood_tag = None
        else:
            mood_tag = request.form.get('mood_tag')
            mood_level = MOOD_TAGS.get(mood_tag, 5)

        # 画像処理
        file = request.files.get('image')
        image_path = None
        f = request.files.get("image")
        if f and f.filename:
            image_path = upload_image_to_gcs(f)  # 例: 'uploads/uuid.png'
    # ← ここでDBに content, genre, mood_tag, image_path を保存
        return redirect(url_for("complete"))

        if file and allowed_file(file.filename):
            fname = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            fname = f"{timestamp}_{fname}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            file.save(save_path)
            image_path = f"uploads/{fname}"

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO diary (content, sentiment, main_category, mood_tag, mood_level, image_path, created_at)
            VALUES (?, NULL, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (content, main_category, mood_tag, mood_level, image_path))
        conn.commit(); conn.close()

        flash('🌟投稿完了したよ！')
        return redirect(url_for('index'))

    # GET: テンプレにカテゴリ配列を渡す
    return render_template('new_diary.html', main_category=MAIN_CATEGORIES)

@app.route("/diary/mood", methods=["POST"])
def diary_mood_legacy():
    flash("フォームが古いバージョンです。ページを更新してください。")
    return redirect(url_for("new_diary"))

@app.route("/stats")
def stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # created_at, mood_level, main_category の順で渡す
    c.execute("SELECT created_at, COALESCE(mood_level, 5), main_category FROM diary ORDER BY created_at ASC")
    data = c.fetchall()
    conn.close()
    # テンプレが使いやすいよう配列で
    packed = [[d[0], int(d[1]), d[2]] for d in data]
    return render_template("stats.html", data=packed)

@app.route("/calendar")
def calendar_view():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, content, main_category, COALESCE(mood_level,5) AS mood_level, created_at
        FROM diary
        ORDER BY created_at
    """)
    rows = c.fetchall()
    conn.close()

    CATEGORY_ICON_PATHS = {
        "日常・ライフログ": "icons/daily.svg",
        "趣味・推し活":     "icons/oshikatsu.svg",
        "家族・育児":       "icons/family.svg",
        "ポジティブログ":   "icons/positiblog.svg",
        "パートナー・恋愛": "icons/partner.svg",
    }

    events = []
    for r in rows:
        lv = int(r["mood_level"] or 5)
        raw = (r["content"] or "")
        snippet = (raw[:10] + "…") if len(raw) > 10 else raw
        icon_path = CATEGORY_ICON_PATHS.get(r["main_category"], "icons/daily.svg")

        events.append({
            "title": f"{EMOJI_MAP.get(lv,'😐')} Lv{lv} {snippet}",
            "start": (r["created_at"] or "").split()[0],
            "url":   url_for("edit_diary", diary_id=r["id"]),
            "iconUrl": url_for("static", filename=icon_path),
            "main_category": r["main_category"],
            "mood_level": lv,
        })
    return render_template("calendar.html", events=events)
    
@app.route("/diary/<date>")
def diary_by_date(date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
      SELECT id, content, sentiment, mood_tag, created_at, image_path, COALESCE(mood_level,5)
      FROM diary
      WHERE DATE(created_at) = ?
      ORDER BY created_at
    """, (date,))
    entries = c.fetchall()
    conn.close()
    return render_template('diary_by_date.html', date=date, entries=entries)
    
@app.route("/edit/<int:diary_id>", methods=["GET", "POST"])
def edit_diary(diary_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == "POST":
        content = request.form.get("content") or ""
        main_category = request.form.get("main_category") or "日常・ライフログ"
        # スライダー優先
        mood_level = clamp_mood(request.form.get("mood_level"))
        mood_tag = request.form.get("mood_tag")  # 任意（旧UI互換）

        c.execute(
            "UPDATE diary SET content=?, main_category=?, mood_tag=?, mood_level=? WHERE id=?",
            (content, main_category, mood_tag, mood_level, diary_id),
        )
        conn.commit()
        conn.close()
        flash("✏️ 日記を保存しました！")
        return redirect(url_for("calendar_view"))

    c.execute("SELECT content, main_category, mood_tag, COALESCE(mood_level,5) FROM diary WHERE id=?", (diary_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "日記が見つかりません", 404

    return render_template(
        "edit_diary.html",
        diary_id=diary_id,
        content=row[0],
        main_category=row[1],
        mood_tag=row[2],
        mood_level=int(row[3]),              # ← これだけ残す
        main_categories=MAIN_CATEGORIES,
        mood_level_labels=MOOD_LEVEL_LABELS
    )

@app.route("/delete/<int:diary_id>", methods=["POST"])
def delete_diary(diary_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM diary WHERE id=?", (diary_id,))
    conn.commit()
    conn.close()
    flash("🗑 日記を削除しました！")
    return redirect(url_for("calendar_view"))

@app.route('/diary/<int:diary_id>')
def diary_detail(diary_id):
    conn = sqlite3.connect('data/diary.db')
    c = conn.cursor()
    c.execute("""
      SELECT content, sentiment, mood_tag, main_category, created_at, image_path
      FROM diary
      WHERE id = ?
    """, (diary_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        flash('その日記は存在しないよ')
        return redirect(url_for('index'))

    # テンプレートに渡す
    return render_template('diary_detail.html',
                           content=row[0],
                           sentiment=row[1],
                           mood_tag=row[2],
                           main_category=row[3],
                           created_at=row[4],
                           image_path=row[5])

# ────────────────────────────────────────────────
#  デバッグ & 起動
# ────────────────────────────────────────────────

@app.route("/debug")
def debug_info():
    return {
        "session": dict(session),
        "db_path": DB_PATH,
        "templates": os.listdir(os.path.join(BASE_DIR, "templates")),
    }


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)