import pandas as pd
import re
import unicodedata

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("combined_news_raw.csv")

# =========================
# TEXT NORMALIZATION
# =========================
def normalize_text(text):
    text = str(text).lower()

    # Remove accents (é → e)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

    # Remove URLs / parentheses
    text = re.sub(r"\(.*?\)", "", text)

    # Remove quotes
    text = text.replace('"', '').replace("'", "")

    # Keep only letters/numbers/spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # -------------------------
    # FIX NUMBERS 
    # -------------------------

    # 1. Fix large numbers (11 000 → 11000)
    text = re.sub(r"\b(\d{1,3})\s(\d{3})\b", r"\1\2", text)

    # 2. Fix versions (2 0 → 2.0)
    text = re.sub(r"\b(\d+)\s+(\d+)\b", r"\1.\2", text)

    # 3. Fix model versions (qwen3 6 → qwen3.6)
    text = re.sub(r"([a-z]+)(\d)\s+(\d)", r"\1\2.\3", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text

df["title_clean"] = df["title"].apply(normalize_text)

# =========================
# FIX COMMON WORD BREAKS
# =========================
replacements = {
    "encyclop dia": "encyclopedia",
    "ch teau": "chateau",
    "io uring": "io_uring",
    "copy paste": "copy-paste",
    "open source": "open-source",
    "ai generated": "ai-generated",
    "qemu kvm": "qemu-kvm"
}

for k, v in replacements.items():
    df["title_clean"] = df["title_clean"].str.replace(k, v, regex=False)

# =========================
# FEATURES
# =========================
df["word_count"] = df["title_clean"].apply(lambda x: len(x.split()))
df["title_length"] = df["title_clean"].apply(len)

# =========================
# TOPIC CLASSIFIER
# =========================
def classify_topic(text):
    text = text.lower()

    # AI FIRST (higher priority)
    if re.search(r"\b(ai|chatgpt|llm|openai|anthropic|neural|model)\b", text):
        return "AI/Technology"

    # SOFTWARE (stronger coverage)
    elif re.search(r"\b(code|software|github|api|linux|compiler|database|cli|tool|server|http|oauth|proxy|cloud|security)\b", text):
        return "Software"

    # SCIENCE / SPACE
    elif re.search(r"\b(mars|nasa|spacex|asteroid|dna|physics|space|science)\b", text):
        return "Space/Science"

    # ECONOMY
    elif re.search(r"\b(economy|market|energy|budget|finance)\b", text):
        return "Economy"

    # HEALTH
    elif re.search(r"\b(health|cancer|drug|disease|heart)\b", text):
        return "Health"

    return "General"

df["topic"] = df["title_clean"].apply(classify_topic)

# =========================
# DATASET LABEL
# =========================
df["dataset"] = "News"

# =========================
# FINAL CLEAN
# =========================
df = df.drop_duplicates().reset_index(drop=True)

# =========================
# SAVE OUTPUT
# =========================
df.to_csv("news_cleaned.csv", index=False)

# =========================
# SUMMARY
# =========================
print("✅ FINAL CLEANING COMPLETE\n")

print("📌 Sample Data:")
print(df.head())

print("\n📊 Topic Distribution:")
print(df["topic"].value_counts())

print("\n📏 Average Title Length:", round(df["title_length"].mean(), 2))
print("🧮 Average Word Count:", round(df["word_count"].mean(), 2))