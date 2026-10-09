import pandas as pd

files = [
    "entertainment.csv",
    "sports.csv",
    "technology.csv",
    "worldnews.csv"
]

df_list = []

for file in files:
    df = pd.read_csv(file)
    df_list.append(df)

combined_df = pd.concat(df_list, ignore_index=True)

combined_df.to_csv("reddit_combined_raw.csv", index=False)

print("Combined dataset created:", len(combined_df))