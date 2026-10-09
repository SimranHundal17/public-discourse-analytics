import requests
from bs4 import BeautifulSoup
import pandas as pd

data = []

# ---------------------------
# 🔵 Hacker News (MULTIPLE PAGES)
# ---------------------------
for page in range(1, 6):  # 5 pages
    url = f"https://news.ycombinator.com/news?p={page}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    titles = soup.find_all("span", class_="titleline")

    for t in titles:
        text = t.get_text().strip()
        if len(text) > 10:
            data.append({
                "title": text,
                "source": "HackerNews"
            })

# ---------------------------
# 🟢 BBC News (FILTERED)
# ---------------------------
url = "https://www.bbc.com/news"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

headlines = soup.find_all("h3")

for h in headlines:
    text = h.get_text().strip()
    
    # filter noise / duplicates
    if len(text) > 20:
        data.append({
            "title": text,
            "source": "BBC"
        })

# ---------------------------
# 🧾 CREATE DATAFRAME
# ---------------------------
df = pd.DataFrame(data)

# remove duplicates
df = df.drop_duplicates()

# save file
df.to_csv("combined_news_raw.csv", index=False)

print("Final news dataset size:", len(df))