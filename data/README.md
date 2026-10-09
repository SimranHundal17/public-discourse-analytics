# Data files and preparation

No raw or cleaned dataset is committed. The project's data folder contained:

- Raw Reddit/news CSVs, including large files approaching 100 MB.
- A cleaned Reddit CSV of about 20 MB with `author` and `url` columns.
- News headlines and institutional/expenditure CSVs.

Even where an individual file is below GitHub's hard per-file limit, its source terms and personal-data implications have not been checked. Do not add datasets until both are reviewed. For a local reproduction, obtain the files through permitted sources and keep them under local, Git-ignored data folders. The dashboard itself expects the loaded MySQL warehouse, not these CSVs.

## Preparation scripts

The scripts are in `preparation/scripts/`. They use relative filenames in the **current working directory**, rather than paths resolved from the script file. Run them only after placing the relevant source CSV in the directory from which the command is run:

| Script | Expected input(s) | Output |
|---|---|---|
| `combined_dataset.py` | `entertainment.csv`, `sports.csv`, `technology.csv`, `worldnews.csv` | `reddit_combined_raw.csv` |
| `clean_reddit.py` | `reddit_time_ready_raw.csv` | `reddit_cleaned.csv` |
| `combined_news_dataset.py` | No local input; requests Hacker News and BBC pages | `combined_news_raw.csv` |
| `clean_news.py` | `combined_news_raw.csv` | `news_cleaned.csv` |
| `institutional_api.py` | No local input; requests World Bank API indicators | `institutional_api_topics.csv` |
| `clean_institutional_api.py` | `institutional_api_topics.csv` | `institutional_cleaned.csv` |
| `clean_worldExpenditure.py` | `WorldExpenditures.csv` | `world_expenditure_cleaned.csv` |

To avoid mixing raw and derived files, run each script from a dedicated working directory and move generated outputs into your local data folders only after checking the script output. These scripts have not been run as part of assembling this repository. Collection results can change over time; some original scripts do not set request timeouts or document a collection date.

## Warehouse dependency

The final app requires the MySQL warehouse tables listed in the root README. The warehouse schema, staging, and ETL SQL are not included in this repository. Do not treat the CSVs or `sql/dashboard_queries.sql` as sufficient to initialize that database.
