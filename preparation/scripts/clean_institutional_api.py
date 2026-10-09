import pandas as pd

df = pd.read_csv("institutional_api_topics.csv")

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = df.dropna()

df = df[(df["year"] >= 2020) & (df["year"] <= 2023)]

df = df[~df["country"].str.contains("Africa|World|income|IDA|IBRD", case=False, na=False)]

df["country"] = df["country"].str.strip()
df["topic"] = df["topic"].str.lower().str.strip()

df = df.sort_values(by=["country", "year", "topic"])

df.to_csv("institutional_cleaned.csv", index=False)