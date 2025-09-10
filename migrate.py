import sqlite3

conn = sqlite3.connect("data/diary.db")
c = conn.cursor()

# 既存カラム一覧を取得
c.execute("PRAGMA table_info(diary)")
columns = [col[1] for col in c.fetchall()]

# user_emotion が無ければ追加
if "user_emotion" not in columns:
    c.execute("ALTER TABLE diary ADD COLUMN user_emotion TEXT")
    print("user_emotion カラムを追加しました！")
else:
    print("user_emotion カラムは既に存在しています。")

# sentiment_score が無ければ追加
if "sentiment_score" not in columns:
    c.execute("ALTER TABLE diary ADD COLUMN sentiment_score REAL")
    print("sentiment_score カラムを追加しました！")
else:
    print("sentiment_score カラムは既に存在しています。")
c.execute("PRAGMA table_info(diary)")
cols = [col[1] for col in c.fetchall()]

if "image_path" not in cols:
    c.execute("ALTER TABLE diary ADD COLUMN image_path TEXT")
    print("image_path カラムを追加したよ！")
else:
    print("もうあるみたい！")
conn.commit()
conn.close()
