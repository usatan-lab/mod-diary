import sqlite3, pandas as pd, os
DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'diary.db')

with sqlite3.connect(DB) as conn:
    df = pd.read_sql_query(
        "SELECT content, mood_tag AS label, sentiment AS ai_label FROM diary WHERE mood_tag!=''", conn
    )
df.to_csv('diary_training_data.csv', index=False, encoding='utf-8')
print("書き出しました → diary_training_data.csv")