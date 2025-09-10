from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re

# モデルとトークナイザの読み込み
model_name = "Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# 感情ラベル（モデルの順番通り）
labels = [
    "joy", "trust", "fear", "surprise", "sadness", "disgust", "anger", "anticipation"
]

# 感情に応じたひとことリアクション
reaction_map = {
    "joy": "楽しそうだね！✨",
    "trust": "信頼できる時間だったのかな？",
    "fear": "ちょっと不安だった？💭",
    "surprise": "びっくりしたことがあったんだね！😲",
    "sadness": "もしかして、つらかった？😢",
    "disgust": "イヤな気分になっちゃったのかも…💦",
    "anger": "むかっときた感じ…？💢",
    "anticipation": "何か楽しみにしてるのかな？😌"
}

# 文を日本語で分割
def split_text_into_sentences(text):
    sentences = re.split(r'[。！？\n]', text)
    return [s.strip() for s in sentences if s.strip()]


# 感情分析（感情＋ひとことリアクションを返す）
def analyze_sentiment(text):
    sentences = split_text_into_sentences(text)
    emotion_scores = {label: 0.0 for label in labels}

    for sentence in sentences:
        inputs = tokenizer(sentence, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            scores = torch.nn.functional.softmax(outputs.logits, dim=1)[0]
            for i, label in enumerate(labels):
                emotion_scores[label] += scores[i].item()

    if emotion_scores["sadness"] > 0.3:
        emotion = "sadness"
    elif emotion_scores["anger"] > 0.3:
        emotion = "anger"
    else:
        emotion = max(emotion_scores, key=emotion_scores.get)

    message = reaction_map.get(emotion, "")
    return emotion, message

def compliment_for(genre, sentiment, character="ねこ"):
    """
    感情分析結果に基づいてほめ言葉を返す関数
    """
    messages = {
        "positive": {
            "一般": "とっても良い感じだね！",
            "推し活": "推しとの素敵な時間を過ごせたんだね！",
            "日常": "今日はいい一日だったんだね！",
            "子供": "子供との時間って特別だよね！",
            "ペット": "ペットとの時間は癒されるね！",
            "恋愛": "素敵な恋愛の時間だったんだね！"
        },
        "neutral": {
            "一般": "いつもどおりの一日だったかな？",
            "推し活": "推しのことを考える時間は大切だよね",
            "日常": "平和な日常も素晴らしいものだよ",
            "子供": "子供の成長を見守る日々は貴重だね",
            "ペット": "ペットと過ごす穏やかな時間いいね",
            "恋愛": "二人の関係、大切にしていこうね"
        },
        "negative": {
            "一般": "大変だったけど、書き出せてえらいね！",
            "推し活": "推しのことを思うだけで明日も頑張れるよ！",
            "日常": "つらい日もあるけど、明日はきっといい日になるよ",
            "子供": "子育ては大変だけど、あなたは頑張ってるよ！",
            "ペット": "ペットのことを思う気持ちは素晴らしいよ",
            "恋愛": "恋愛も時には難しいけど、きっと良くなるよ"
        }
    }
    
    # もしジャンルが辞書になければ一般を使用
    if genre not in messages[sentiment]:
        genre = "一般"
    
    # キャラクターに合わせた語尾を追加
    endings = {
        "ねこ": "にゃ～",
        "いぬ": "わん！",
        "うさぎ": "ぴょん♪",
        "ペンギン": "ぺん！",
        "くま": "くまー"
    }
    
    ending = endings.get(character, "")
    return messages[sentiment][genre] + " " + ending
