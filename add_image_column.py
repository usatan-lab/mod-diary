import sqlite3

# DB パスは app.py と同じになるように
conn = sqlite3.connect('data/diary.db')
c = conn.cursor()

# 既存カラムの確認
c.execute("PRAGMA table_info(diary)")
cols = [col[1] for col in c.fetchall()]

if "image_path" not in cols:
    c.execute("ALTER TABLE diary ADD COLUMN image_path TEXT")
    print("✅ image_path カラムを追加したよ！")
else:
    print("⚠️ image_path は既に存在してるみたい！")

conn.commit()
conn.close()
