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

# 文を日本語で分割
def split_text_into_sentences(text):
    sentences = re.split(r'[。！？\n]', text)
    return [s.strip() for s in sentences if s.strip()]

# 感情分析（悲しみがある場合は優先するロジック付き）
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

    # 💡 特定の感情が一定以上ある場合は優先的に返す
    if emotion_scores["sadness"] > 0.3:
        return "sadness"
    if emotion_scores["anger"] > 0.3:
        return "anger"

    # 通常はスコア最大の感情を返す
    max_emotion = max(emotion_scores, key=emotion_scores.get)
    return max_emotion
