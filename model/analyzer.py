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
