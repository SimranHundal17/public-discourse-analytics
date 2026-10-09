import pandas as pd
import re

# load dataset
df = pd.read_csv("reddit_time_ready_raw.csv")

print("Initial shape:", df.shape)

# -------------------------
# 1. REMOVE DUPLICATES
# -------------------------
df = df.drop_duplicates(subset=["title", "url"])

# -------------------------
# 2. HANDLE MISSING VALUES
# -------------------------
df = df.dropna(subset=["title", "utc_datetime_str"])

# -------------------------
# 3. REMOVE LOW-QUALITY / SPAM CONTENT
# -------------------------

# remove deleted users
df = df[df["author"] != "[deleted]"]

# remove spam keywords in titles
spam_keywords = ["escort", "onlyfans", "blogspot", "watch", "free", "click", "subscribe"]
df = df[~df["title"].str.lower().str.contains("|".join(spam_keywords), na=False)]

# remove spam domains in URLs
bad_domains = ["adarose", "blogspot", "amazon", "shorturl"]
df = df[~df["url"].str.contains('|'.join(bad_domains), case=False, na=False)]

# remove very short & very long titles
df["title_length_raw"] = df["title"].str.len()
df = df[(df["title_length_raw"] > 15) & (df["title_length_raw"] < 200)]

# -------------------------
# 4. TEXT CLEANING
# -------------------------
df["title_clean"] = df["title"].str.lower()

# remove special characters
df["title_clean"] = df["title_clean"].apply(lambda x: re.sub(r"[^a-zA-Z0-9\s]", "", x))

# remove HTML artifacts
df["title_clean"] = df["title_clean"].str.replace("amp", "")

# remove extra spaces
df["title_clean"] = df["title_clean"].str.strip()

# -------------------------
# 5. DATE STANDARDIZATION
# -------------------------
df["date"] = pd.to_datetime(df["utc_datetime_str"], errors="coerce")
df = df.dropna(subset=["date"])

df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day

# -------------------------
# 6. FEATURE ENGINEERING
# -------------------------

# title length
df["title_length"] = df["title_clean"].str.len()

# word count
df["word_count"] = df["title_clean"].str.split().apply(len)

# -------------------------
# 7. REMOVE DUPLICATE CONTENT (IMPORTANT)
# -------------------------
df = df.drop_duplicates(subset=["title_clean"])

# -------------------------
# 8. IMPROVED TOPIC CLASSIFICATION
# -------------------------
def classify_topic(text):
    text = text.lower()
    
    if any(word in text for word in ["movie", "film", "netflix", "series", "episode", "tv"]):
        return "Movies/TV"
    elif any(word in text for word in ["music", "song", "album", "concert", "rapper"]):
        return "Music"
    elif any(word in text for word in ["celebrity", "actor", "actress", "award", "oscars"]):
        return "Celebrities"
    elif any(word in text for word in ["politics", "government", "election", "president"]):
        return "Politics"
    else:
        return "Other"

df["topic"] = df["title_clean"].apply(classify_topic)

# -------------------------
# 9. ENGAGEMENT PROXY
# -------------------------
df["engagement_score"] = df["word_count"]

# -------------------------
# 10. FINAL CLEANUP
# -------------------------
df = df.reset_index(drop=True)

print("Final shape:", df.shape)

# save cleaned dataset
df.to_csv("reddit_cleaned.csv", index=False)

print("Reddit cleaning completed successfully!")