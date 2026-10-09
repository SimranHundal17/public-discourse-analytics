import os
from decimal import Decimal

from flask import Flask, jsonify, render_template, request
import mysql.connector
from mysql.connector import Error


app = Flask(__name__)


def load_local_env(path=".env"):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "public_discourse"),
}


REDDIT_TOPIC_CASE = """
CASE
    WHEN LOWER(title) REGEXP 'ai|artificial intelligence|chatgpt|machine learning|technology|software|computer|app|data|internet|google|microsoft|apple|digital|cyber|programming|developer|code|robot|automation'
        THEN 'AI/Technology'
    WHEN LOWER(title) REGEXP 'movie|film|netflix|series|episode|tv|actor|actress|celebrity|hollywood|music|song|album|concert|rapper|singer|award|oscar|hbo|disney|trailer'
        THEN 'Entertainment'
    WHEN LOWER(title) REGEXP 'politics|government|election|president|minister|policy|law|vote|parliament|congress|ukraine|russia|china|war|nato|israel'
        THEN 'Politics'
    WHEN LOWER(title) REGEXP 'economy|business|market|stock|inflation|money|bank|finance|job|jobs|company|startup|investment|tax'
        THEN 'Economy'
    WHEN LOWER(title) REGEXP 'health|doctor|hospital|disease|covid|medicine|mental|therapy|drug|healthcare|medical'
        THEN 'Health'
    WHEN LOWER(title) REGEXP 'education|school|university|student|college|teacher|learning|exam|course'
        THEN 'Education'
    WHEN LOWER(title) REGEXP 'football|soccer|basketball|cricket|tennis|nba|fifa|sport|sports|league|match|tournament'
        THEN 'Sports'
    WHEN LOWER(title) REGEXP 'climate|environment|energy|pollution|carbon|green|weather|sustainability'
        THEN 'Environment'
    WHEN LOWER(title) REGEXP 'space|science|nasa|spacex|mars|moon|research|scientist|physics|biology'
        THEN 'Space/Science'
    WHEN LOWER(title) REGEXP 'crime|police|court|trial|murder|arrest|safety|violence'
        THEN 'Safety'
    ELSE 'Other'
END
"""

TOPIC_LIST_SQL = """
SELECT 'AI/Technology' AS topic_name
UNION SELECT 'Entertainment'
UNION SELECT 'Politics'
UNION SELECT 'Economy'
UNION SELECT 'Health'
UNION SELECT 'Education'
UNION SELECT 'Sports'
UNION SELECT 'Environment'
UNION SELECT 'Space/Science'
UNION SELECT 'Safety'
"""


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


def clean_value(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def clean_rows(rows):
    return [{key: clean_value(value) for key, value in row.items()} for row in rows]


def execute_query(query, params=None, single=False):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or [])
        rows = clean_rows(cursor.fetchall())
        return (rows[0] if rows else {}) if single else rows
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


def table_columns(table_name):
    query = """
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = %s
      AND TABLE_NAME = %s;
    """
    rows = execute_query(query, [DB_CONFIG["database"], table_name])
    return {row["COLUMN_NAME"] for row in rows}


def api_success(data):
    return jsonify({"success": True, "data": data})


def api_error(error):
    app.logger.error("Database API error: %s", error)
    return jsonify({"success": False, "error": str(error), "data": None}), 500


def country_param(default="Germany"):
    return request.args.get("country", default).strip() or default


def normalize_topic_name(topic_name):
    topic_map = {
        "education": "Education",
        "environment": "Environment",
        "safety": "Safety",
    }
    return topic_map.get(str(topic_name), topic_map.get(str(topic_name).lower(), topic_name))


@app.route("/")
def index():
    return render_template("index.html", database_name=DB_CONFIG["database"])


@app.route("/api/countries")
def countries():
    try:
        return api_success(
            execute_query(
                """
                SELECT country_name
                FROM dim_countries
                ORDER BY country_name;
                """
            )
        )
    except Error as exc:
        return api_error(exc)


@app.route("/api/public/kpis")
def public_kpis():
    try:
        query = """
        SELECT
            (SELECT COUNT(*) FROM fact_reddit_posts) AS total_reddit_posts,
            (SELECT COUNT(*) FROM fact_news_articles) AS total_news_articles,
            (
                (SELECT COUNT(*) FROM fact_reddit_posts) +
                (SELECT COUNT(*) FROM fact_news_articles)
            ) AS total_public_discourse_records,
            (SELECT COUNT(*) FROM dim_topics) AS total_topics;
        """
        return api_success(execute_query(query, single=True))
    except Error as exc:
        return api_error(exc)


@app.route("/api/public/discourse-by-topic")
def public_discourse_by_topic():
    try:
        query = f"""
        SELECT
            topics.topic_name,
            COALESCE(reddit.reddit_posts, 0) AS reddit_posts,
            COALESCE(news.news_articles, 0) AS news_articles,
            COALESCE(reddit.reddit_posts, 0) + COALESCE(news.news_articles, 0) AS total_records
        FROM ({TOPIC_LIST_SQL}) topics
        LEFT JOIN (
            SELECT dashboard_topic AS topic_name, COUNT(*) AS reddit_posts
            FROM (
                SELECT {REDDIT_TOPIC_CASE} AS dashboard_topic
                FROM fact_reddit_posts
            ) r
            WHERE dashboard_topic NOT IN ('Other', 'General')
            GROUP BY dashboard_topic
        ) reddit ON topics.topic_name = reddit.topic_name
        LEFT JOIN (
            SELECT
                CASE
                    WHEN LOWER(t.topic_name) = 'education' THEN 'Education'
                    WHEN LOWER(t.topic_name) = 'environment' THEN 'Environment'
                    WHEN LOWER(t.topic_name) = 'safety' THEN 'Safety'
                    ELSE t.topic_name
                END AS topic_name,
                COUNT(n.news_id) AS news_articles
            FROM fact_news_articles n
            JOIN dim_topics t ON n.topic_id = t.topic_id
            WHERE t.topic_name NOT IN ('Other', 'General')
            GROUP BY topic_name
        ) news ON topics.topic_name = news.topic_name
        WHERE COALESCE(reddit.reddit_posts, 0) + COALESCE(news.news_articles, 0) > 0
        ORDER BY total_records DESC;
        """
        return api_success(execute_query(query))
    except Error as exc:
        return api_error(exc)


@app.route("/api/public/share-by-topic")
def public_share_by_topic():
    try:
        rows = execute_query(
            """
            SELECT topic_name, total_records
            FROM (
                SELECT
                    t.topic_name,
                    COUNT(n.news_id) AS total_records
                FROM fact_news_articles n
                JOIN dim_topics t ON n.topic_id = t.topic_id
                WHERE t.topic_name NOT IN ('Other', 'General')
                GROUP BY t.topic_name
            ) x
            ORDER BY total_records DESC;
            """
        )
        reddit_rows = execute_query(
            f"""
            SELECT dashboard_topic AS topic_name, COUNT(*) AS total_records
            FROM (
                SELECT {REDDIT_TOPIC_CASE} AS dashboard_topic
                FROM fact_reddit_posts
            ) r
            WHERE dashboard_topic NOT IN ('Other', 'General')
            GROUP BY dashboard_topic;
            """
        )
        totals = {}
        for row in rows + reddit_rows:
            topic = normalize_topic_name(row["topic_name"])
            totals[topic] = totals.get(topic, 0) + row["total_records"]
        total = sum(totals.values()) or 1
        data = [
            {"topic_name": topic, "share": round((value / total) * 100, 2), "total_records": value}
            for topic, value in sorted(totals.items(), key=lambda item: item[1], reverse=True)
        ]
        return api_success(data)
    except Error as exc:
        return api_error(exc)


@app.route("/api/public/monthly-reddit-trend")
def monthly_reddit_trend():
    try:
        columns = table_columns("dim_time")
        if "month" in columns:
            month_label_sql = "CONCAT(d.year, '-', LPAD(d.month, 2, '0'))"
            group_filter_sql = "d.year IN (2022, 2023)"
            order_sql = "month_label, topic_name"
        elif "date" in columns:
            month_label_sql = "DATE_FORMAT(d.date, '%Y-%m')"
            group_filter_sql = "YEAR(d.date) IN (2022, 2023)"
            order_sql = "month_label, topic_name"
        elif "full_date" in columns:
            month_label_sql = "DATE_FORMAT(d.full_date, '%Y-%m')"
            group_filter_sql = "YEAR(d.full_date) IN (2022, 2023)"
            order_sql = "month_label, topic_name"
        else:
            month_label_sql = "CAST(d.year AS CHAR)"
            group_filter_sql = "d.year IN (2022, 2023)"
            order_sql = "month_label, topic_name"

        query = f"""
        SELECT
            {REDDIT_TOPIC_CASE} AS topic_name,
            {month_label_sql} AS month_label,
            COUNT(r.reddit_id) AS reddit_posts
        FROM fact_reddit_posts r
        JOIN dim_time d ON r.time_id = d.time_id
        WHERE {group_filter_sql}
        GROUP BY topic_name, month_label
        HAVING topic_name NOT IN ('Other', 'General')
        ORDER BY {order_sql};
        """
        return api_success(execute_query(query))
    except Error as exc:
        return api_error(exc)


@app.route("/api/institutional/kpis")
def institutional_kpis():
    try:
        query = """
        SELECT
            (SELECT COUNT(*) FROM dim_countries) AS total_countries,
            (SELECT COUNT(DISTINCT year) FROM dim_time) AS total_years,
            (SELECT COUNT(*) FROM fact_government_expenditure) AS expenditure_records,
            (SELECT COUNT(*) FROM fact_institutional_metrics) AS institutional_records;
        """
        return api_success(execute_query(query, single=True))
    except Error as exc:
        return api_error(exc)


@app.route("/api/institutional/government-expenditure-by-topic")
def government_expenditure_by_topic():
    try:
        query = """
        SELECT
            t.topic_name,
            ROUND(AVG(g.value), 2) AS avg_expenditure
        FROM fact_government_expenditure g
        JOIN dim_topics t ON g.topic_id = t.topic_id
        WHERE t.topic_name NOT IN ('Other', 'General')
        GROUP BY t.topic_name
        ORDER BY avg_expenditure DESC;
        """
        return api_success(execute_query(query))
    except Error as exc:
        return api_error(exc)


@app.route("/api/institutional/metrics-by-topic")
def institutional_metrics_by_topic():
    try:
        query = """
        SELECT
            t.topic_name,
            ROUND(AVG(i.value), 2) AS avg_institutional_value
        FROM fact_institutional_metrics i
        JOIN dim_topics t ON i.topic_id = t.topic_id
        WHERE t.topic_name NOT IN ('Other', 'General')
        GROUP BY t.topic_name
        ORDER BY avg_institutional_value DESC;
        """
        return api_success(execute_query(query))
    except Error as exc:
        return api_error(exc)


@app.route("/api/institutional/top-expenditure-countries")
def top_expenditure_countries():
    try:
        query = """
        SELECT
            c.country_name,
            ROUND(SUM(g.value), 2) AS total_expenditure
        FROM fact_government_expenditure g
        JOIN dim_countries c ON g.country_id = c.country_id
        GROUP BY c.country_name
        ORDER BY total_expenditure DESC
        LIMIT 10;
        """
        return api_success(execute_query(query))
    except Error as exc:
        return api_error(exc)


@app.route("/api/institutional/top-metric-countries")
def top_metric_countries():
    try:
        query = """
        SELECT
            c.country_name,
            ROUND(AVG(i.value), 2) AS avg_institutional_value
        FROM fact_institutional_metrics i
        JOIN dim_countries c ON i.country_id = c.country_id
        GROUP BY c.country_name
        ORDER BY avg_institutional_value DESC
        LIMIT 10;
        """
        return api_success(execute_query(query))
    except Error as exc:
        return api_error(exc)


@app.route("/api/institutional/spending-vs-performance")
def spending_vs_performance():
    try:
        query = """
        SELECT
            c.country_name,
            COALESCE(exp.total_expenditure, 0) AS total_expenditure,
            COALESCE(inst.avg_institutional_value, 0) AS avg_institutional_value
        FROM dim_countries c
        LEFT JOIN (
            SELECT country_id, ROUND(SUM(value), 2) AS total_expenditure
            FROM fact_government_expenditure
            GROUP BY country_id
        ) exp ON c.country_id = exp.country_id
        LEFT JOIN (
            SELECT country_id, ROUND(AVG(value), 2) AS avg_institutional_value
            FROM fact_institutional_metrics
            GROUP BY country_id
        ) inst ON c.country_id = inst.country_id
        WHERE COALESCE(exp.total_expenditure, 0) > 0
           OR COALESCE(inst.avg_institutional_value, 0) > 0
        ORDER BY total_expenditure DESC;
        """
        return api_success(execute_query(query))
    except Error as exc:
        return api_error(exc)


@app.route("/api/country-expenditure")
def country_expenditure():
    try:
        query = """
        SELECT
            c.country_name,
            t.topic_name,
            ROUND(SUM(g.value), 2) AS total_expenditure
        FROM fact_government_expenditure g
        JOIN dim_countries c ON g.country_id = c.country_id
        JOIN dim_topics t ON g.topic_id = t.topic_id
        WHERE c.country_name = %s
          AND t.topic_name NOT IN ('Other', 'General')
        GROUP BY c.country_name, t.topic_name
        ORDER BY total_expenditure DESC;
        """
        return api_success(execute_query(query, [country_param()]))
    except Error as exc:
        return api_error(exc)


@app.route("/api/country-institutional")
def country_institutional():
    try:
        query = """
        SELECT
            c.country_name,
            t.topic_name,
            ROUND(AVG(i.value), 2) AS avg_institutional_value
        FROM fact_institutional_metrics i
        JOIN dim_countries c ON i.country_id = c.country_id
        JOIN dim_topics t ON i.topic_id = t.topic_id
        WHERE c.country_name = %s
          AND t.topic_name NOT IN ('Other', 'General')
        GROUP BY c.country_name, t.topic_name
        ORDER BY avg_institutional_value DESC;
        """
        return api_success(execute_query(query, [country_param()]))
    except Error as exc:
        return api_error(exc)


@app.route("/api/alignment/share-comparison")
def alignment_share_comparison():
    try:
        return api_success(execute_query(alignment_query()))
    except Error as exc:
        return api_error(exc)


@app.route("/api/alignment/priority-gap")
def priority_gap():
    try:
        rows = execute_query(alignment_query())
        rows.sort(key=lambda row: row["priority_gap"], reverse=True)
        return api_success(rows)
    except Error as exc:
        return api_error(exc)


@app.route("/api/alignment/insights")
def alignment_insights():
    try:
        rows = execute_query(alignment_query())
        public_topics = [row for row in rows if row["priority_gap"] > 0]
        government_topics = [row for row in rows if row["priority_gap"] < 0]
        biggest = sorted(rows, key=lambda row: abs(row["priority_gap"]), reverse=True)[:3]
        return api_success(
            {
                "higher_public_attention": public_topics[:3],
                "higher_government_priority": government_topics[:3],
                "biggest_gaps": biggest,
            }
        )
    except Error as exc:
        return api_error(exc)


def alignment_query():
    return f"""
    SELECT
        topics.topic_name,
        ROUND(COALESCE(public_counts.public_records, 0) / NULLIF(public_total.total_public, 0) * 100, 2) AS public_share,
        ROUND(COALESCE(gov_counts.gov_expenditure, 0) / NULLIF(gov_total.total_government, 0) * 100, 2) AS government_share,
        ROUND(
            (COALESCE(public_counts.public_records, 0) / NULLIF(public_total.total_public, 0) * 100) -
            (COALESCE(gov_counts.gov_expenditure, 0) / NULLIF(gov_total.total_government, 0) * 100),
            2
        ) AS priority_gap
    FROM ({TOPIC_LIST_SQL}) topics
    LEFT JOIN (
        SELECT topic_name, SUM(records) AS public_records
        FROM (
            SELECT dashboard_topic AS topic_name, COUNT(*) AS records
            FROM (
                SELECT {REDDIT_TOPIC_CASE} AS dashboard_topic
                FROM fact_reddit_posts
            ) r
            WHERE dashboard_topic NOT IN ('Other', 'General')
            GROUP BY dashboard_topic
            UNION ALL
            SELECT
                CASE
                    WHEN LOWER(t.topic_name) = 'education' THEN 'Education'
                    WHEN LOWER(t.topic_name) = 'environment' THEN 'Environment'
                    WHEN LOWER(t.topic_name) = 'safety' THEN 'Safety'
                    ELSE t.topic_name
                END AS topic_name,
                COUNT(n.news_id) AS records
            FROM fact_news_articles n
            JOIN dim_topics t ON n.topic_id = t.topic_id
            WHERE t.topic_name NOT IN ('Other', 'General')
            GROUP BY topic_name
        ) combined_public
        GROUP BY topic_name
    ) public_counts ON topics.topic_name = public_counts.topic_name
    LEFT JOIN (
        SELECT
            CASE
                WHEN LOWER(t.topic_name) = 'education' THEN 'Education'
                WHEN LOWER(t.topic_name) = 'environment' THEN 'Environment'
                WHEN LOWER(t.topic_name) = 'safety' THEN 'Safety'
                ELSE t.topic_name
            END AS topic_name,
            SUM(g.value) AS gov_expenditure
        FROM fact_government_expenditure g
        JOIN dim_topics t ON g.topic_id = t.topic_id
        WHERE t.topic_name NOT IN ('Other', 'General')
        GROUP BY topic_name
    ) gov_counts ON topics.topic_name = gov_counts.topic_name
    CROSS JOIN (
        SELECT SUM(records) AS total_public
        FROM (
            SELECT COUNT(*) AS records
            FROM (
                SELECT {REDDIT_TOPIC_CASE} AS dashboard_topic
                FROM fact_reddit_posts
            ) r
            WHERE dashboard_topic NOT IN ('Other', 'General')
            UNION ALL
            SELECT COUNT(n.news_id) AS records
            FROM fact_news_articles n
            JOIN dim_topics t ON n.topic_id = t.topic_id
            WHERE t.topic_name NOT IN ('Other', 'General')
        ) all_public
    ) public_total
    CROSS JOIN (
        SELECT SUM(g.value) AS total_government
        FROM fact_government_expenditure g
        JOIN dim_topics t ON g.topic_id = t.topic_id
        WHERE t.topic_name NOT IN ('Other', 'General')
    ) gov_total
    WHERE COALESCE(public_counts.public_records, 0) > 0
       OR COALESCE(gov_counts.gov_expenditure, 0) > 0
    ORDER BY public_share DESC;
    """


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
