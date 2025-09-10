def translate_emotion(sentiment):
    translations = {
        "positive": "ポジティブ",
        "neutral": "普通",
        "negative": "ネガティブ",
        "happy": "ハッピー",
        "sad": "悲しい",
        "angry": "怒り",
        "anxious": "不安",
        "grateful": "感謝",
        "touched": "感動",
        "tired": "疲れ",
        "excited": "ワクワク",
        "calm": "穏やか",
        "lonely": "さみしい",
        "surprised": "びっくり"
    }

    return translations.get(sentiment, "不明")
