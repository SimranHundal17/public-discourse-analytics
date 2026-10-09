import pandas as pd

df = pd.read_csv("WorldExpenditures.csv")

df.columns = ["index", "year", "country", "sector", "expenditure", "gdp_percent"]

df = df.drop(columns=["index"])

df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["expenditure"] = pd.to_numeric(df["expenditure"], errors="coerce")
df["gdp_percent"] = pd.to_numeric(df["gdp_percent"], errors="coerce")

df = df.dropna()

df = df[(df["year"] >= 2020) & (df["year"] <= 2023)]

df["sector"] = df["sector"].str.lower().str.strip()
df["country"] = df["country"].str.strip()

mapping = {
    "health": "health",
    "education": "education",
    "defence": "defense",
    "environment protection": "environment",
    "housing and community amenities": "housing",
    "transport": "transport",
    "social protection": "social",
    "public order and safety": "safety"
}

df["topic"] = df["sector"].map(mapping)

df = df.dropna(subset=["topic"])

df = df[["country", "year", "topic", "gdp_percent"]]

df = df.rename(columns={"gdp_percent": "value"})

df = df.sort_values(by=["country", "year", "topic"])

df.to_csv("world_expenditure_cleaned.csv", index=False)