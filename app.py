from flask import Flask, render_template, request, redirect
import sqlite3
from model.analyzer import analyze_sentiment
from datetime import datetime
import os

app = Flask(__name__)

# DB初期化
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect('data/diary.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS diary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                sentiment TEXT,
                created_at TEXT
            )''')
conn.commit()
conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    if request.method == 'POST':
        content = request.form['content']
        sentiment, message = analyze_sentiment(content)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect('data/diary.db')
        c = conn.cursor()
        c.execute("INSERT INTO diary (content, sentiment, created_at) VALUES (?, ?, ?)",
                  (content, sentiment, created_at))
        conn.commit()
        conn.close()
        return redirect('/')

    conn = sqlite3.connect('data/diary.db')
    c = conn.cursor()
    c.execute("SELECT content, sentiment, created_at FROM diary ORDER BY created_at DESC")
    entries = c.fetchall()
    conn.close()
    return render_template('index.html', entries=entries, message=message)

if __name__ == '__main__':
    app.run(debug=True)