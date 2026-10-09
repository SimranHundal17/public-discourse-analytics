-- Select your warehouse database first, e.g. USE your_database_name;

-- =====================================================
-- DASHBOARD SQL QUERIES
-- Schema used:
-- dim_topics, dim_countries, dim_time
-- fact_reddit_posts, fact_news_articles
-- fact_government_expenditure, fact_institutional_metrics
-- =====================================================


-- =====================================================
-- TAB 1: PUBLIC DISCOURSE DASHBOARD
-- Reddit + News combined
-- =====================================================

-- QUERY 1: Public Discourse KPI Cards
SELECT
    (SELECT COUNT(*) FROM fact_reddit_posts) AS total_reddit_posts,
    (SELECT COUNT(*) FROM fact_news_articles) AS total_news_articles,
    ((SELECT COUNT(*) FROM fact_reddit_posts) +
     (SELECT COUNT(*) FROM fact_news_articles)) AS total_public_discourse_records,
    (SELECT COUNT(*) FROM dim_topics) AS total_topics;


-- QUERY 2: Public Discourse by Topic
-- Combines Reddit + News into one public attention score.
-- Reddit is classified using title keywords.
-- News uses existing topic_id from dim_topics.
SELECT
    topic_name,
    SUM(public_count) AS total_public_discourse
FROM
(
    SELECT
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
                THEN 'education'
            WHEN LOWER(title) REGEXP 'football|soccer|basketball|cricket|tennis|nba|fifa|sport|sports|league|match|tournament'
                THEN 'Sports'
            WHEN LOWER(title) REGEXP 'climate|environment|energy|pollution|carbon|green|weather|sustainability'
                THEN 'environment'
            WHEN LOWER(title) REGEXP 'space|science|nasa|spacex|mars|moon|research|scientist|physics|biology'
                THEN 'Space/Science'
            WHEN LOWER(title) REGEXP 'crime|police|court|trial|murder|arrest|safety|violence'
                THEN 'safety'
            ELSE 'Other'
        END AS topic_name,
        COUNT(*) AS public_count
    FROM fact_reddit_posts r
    JOIN dim_time d ON r.time_id = d.time_id
    WHERE d.year IN (2022, 2023)
    GROUP BY topic_name

    UNION ALL

    SELECT
        t.topic_name,
        COUNT(n.news_id) AS public_count
    FROM fact_news_articles n
    JOIN dim_topics t ON n.topic_id = t.topic_id
    GROUP BY t.topic_name
) x
WHERE topic_name NOT IN ('Other', 'General')
GROUP BY topic_name
ORDER BY total_public_discourse DESC;


-- QUERY 3: Public Discourse Share by Topic
-- Used for donut/pie chart.
SELECT
    topic_name,
    total_public_discourse,
    ROUND(total_public_discourse * 100.0 / SUM(total_public_discourse) OVER (), 2) AS percentage_share
FROM
(
    SELECT
        topic_name,
        SUM(public_count) AS total_public_discourse
    FROM
    (
        SELECT
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
                    THEN 'education'
                WHEN LOWER(title) REGEXP 'football|soccer|basketball|cricket|tennis|nba|fifa|sport|sports|league|match|tournament'
                    THEN 'Sports'
                WHEN LOWER(title) REGEXP 'climate|environment|energy|pollution|carbon|green|weather|sustainability'
                    THEN 'environment'
                WHEN LOWER(title) REGEXP 'space|science|nasa|spacex|mars|moon|research|scientist|physics|biology'
                    THEN 'Space/Science'
                WHEN LOWER(title) REGEXP 'crime|police|court|trial|murder|arrest|safety|violence'
                    THEN 'safety'
                ELSE 'Other'
            END AS topic_name,
            COUNT(*) AS public_count
        FROM fact_reddit_posts r
        JOIN dim_time d ON r.time_id = d.time_id
        WHERE d.year IN (2022, 2023)
        GROUP BY topic_name

        UNION ALL

        SELECT
            t.topic_name,
            COUNT(n.news_id) AS public_count
        FROM fact_news_articles n
        JOIN dim_topics t ON n.topic_id = t.topic_id
        GROUP BY t.topic_name
    ) x
    WHERE topic_name NOT IN ('Other', 'General')
    GROUP BY topic_name
) y
ORDER BY total_public_discourse DESC;


-- QUERY 4: Monthly Reddit Topic Trend
-- Multi-line chart: one line per topic.
-- Uses 2022-2023 only and removes the 2009 outlier.
SELECT
    CONCAT(d.year, '-', LPAD(d.month, 2, '0')) AS month_label,
    CASE
        WHEN LOWER(r.title) REGEXP 'ai|artificial intelligence|chatgpt|machine learning|technology|software|computer|app|data|internet|google|microsoft|apple|digital|cyber|programming|developer|code|robot|automation'
            THEN 'AI/Technology'
        WHEN LOWER(r.title) REGEXP 'movie|film|netflix|series|episode|tv|actor|actress|celebrity|hollywood|music|song|album|concert|rapper|singer|award|oscar|hbo|disney|trailer'
            THEN 'Entertainment'
        WHEN LOWER(r.title) REGEXP 'politics|government|election|president|minister|policy|law|vote|parliament|congress|ukraine|russia|china|war|nato|israel'
            THEN 'Politics'
        WHEN LOWER(r.title) REGEXP 'economy|business|market|stock|inflation|money|bank|finance|job|jobs|company|startup|investment|tax'
            THEN 'Economy'
        WHEN LOWER(r.title) REGEXP 'health|doctor|hospital|disease|covid|medicine|mental|therapy|drug|healthcare|medical'
            THEN 'Health'
        ELSE 'Other'
    END AS topic_name,
    COUNT(r.reddit_id) AS reddit_posts
FROM fact_reddit_posts r
JOIN dim_time d ON r.time_id = d.time_id
WHERE d.year IN (2022, 2023)
  AND d.month IS NOT NULL
GROUP BY month_label, topic_name
HAVING topic_name <> 'Other'
ORDER BY month_label, topic_name;


-- =====================================================
-- TAB 2: INSTITUTIONAL PRIORITIES DASHBOARD
-- Government Expenditure + Institutional Metrics
-- =====================================================

-- QUERY 5: Institutional KPI Cards
SELECT
    (SELECT COUNT(*) FROM dim_countries) AS total_countries,
    (SELECT COUNT(DISTINCT year) FROM dim_time) AS total_years,
    (SELECT COUNT(*) FROM fact_government_expenditure) AS expenditure_records,
    (SELECT COUNT(*) FROM fact_institutional_metrics) AS institutional_records;


-- QUERY 6: Government Expenditure by Topic
SELECT
    t.topic_name,
    ROUND(SUM(g.value), 2) AS total_expenditure
FROM fact_government_expenditure g
JOIN dim_topics t ON g.topic_id = t.topic_id
WHERE t.topic_name NOT IN ('Other', 'General')
GROUP BY t.topic_name
ORDER BY total_expenditure DESC;

-- QUERY 7: Institutional Metrics by Topic
SELECT
    t.topic_name,
    ROUND(AVG(i.value), 2) AS avg_institutional_value
FROM fact_institutional_metrics i
JOIN dim_topics t ON i.topic_id = t.topic_id
WHERE t.topic_name NOT IN ('Other', 'General')
GROUP BY t.topic_name
ORDER BY avg_institutional_value DESC;


-- QUERY 8: Top Countries by Government Expenditure
SELECT
    c.country_name,
    ROUND(SUM(g.value), 2) AS total_expenditure
FROM fact_government_expenditure g
JOIN dim_countries c ON g.country_id = c.country_id
GROUP BY c.country_name
ORDER BY total_expenditure DESC
LIMIT 10;


-- QUERY 9: Top Countries by Institutional Metrics
SELECT
    c.country_name,
    ROUND(AVG(i.value), 2) AS avg_institutional_value
FROM fact_institutional_metrics i
JOIN dim_countries c ON i.country_id = c.country_id
GROUP BY c.country_name
ORDER BY avg_institutional_value DESC
LIMIT 10;


-- QUERY 10: Country List for Map / Dropdown
-- Use this to populate selectable countries.
SELECT
    country_id,
    country_name
FROM dim_countries
ORDER BY country_name;


-- QUERY 11: Country Expenditure by Topic
-- Used when a country is selected on map/dropdown.
-- Replace 'Germany' dynamically from Flask.
SELECT
    c.country_name,
    t.topic_name,
    ROUND(SUM(g.value), 2) AS total_expenditure
FROM fact_government_expenditure g
JOIN dim_countries c ON g.country_id = c.country_id
JOIN dim_topics t ON g.topic_id = t.topic_id
WHERE c.country_name = 'Germany'
  AND t.topic_name NOT IN ('Other', 'General')
GROUP BY c.country_name, t.topic_name
ORDER BY total_expenditure DESC;


-- QUERY 12: Country Institutional Metrics by Topic
-- Used when a country is selected.
-- Replace 'Germany' dynamically from Flask.
SELECT
    c.country_name,
    t.topic_name,
    ROUND(AVG(i.value), 2) AS avg_institutional_value
FROM fact_institutional_metrics i
JOIN dim_countries c ON i.country_id = c.country_id
JOIN dim_topics t ON i.topic_id = t.topic_id
WHERE c.country_name = 'Germany'
  AND t.topic_name NOT IN ('Other', 'General')
GROUP BY c.country_name, t.topic_name
ORDER BY avg_institutional_value DESC;


-- QUERY 13: Spending vs Institutional Performance Scatter
-- Each row is one country.
SELECT
    c.country_name,
    ROUND(COALESCE(exp.total_expenditure, 0), 2) AS total_expenditure,
    ROUND(COALESCE(inst.avg_institutional_value, 0), 2) AS avg_institutional_value
FROM dim_countries c
LEFT JOIN (
    SELECT
        country_id,
        SUM(value) AS total_expenditure
    FROM fact_government_expenditure
    GROUP BY country_id
) exp ON c.country_id = exp.country_id
LEFT JOIN (
    SELECT
        country_id,
        AVG(value) AS avg_institutional_value
    FROM fact_institutional_metrics
    GROUP BY country_id
) inst ON c.country_id = inst.country_id
WHERE exp.total_expenditure IS NOT NULL
   OR inst.avg_institutional_value IS NOT NULL
ORDER BY total_expenditure DESC;


-- =====================================================
-- TAB 3: ALIGNMENT COMPARISON DASHBOARD
-- Public Discourse vs Institutional Priorities
-- =====================================================

-- =====================================================
-- QUERY 14: Public Attention vs Government Expenditure
-- =====================================================
-- Purpose:
-- Compare only topics that exist in BOTH datasets.
--
-- Shared Topics:
-- Health
-- education
-- environment
-- safety
--
-- Use:
-- Grouped Bar Chart
-- =====================================================

WITH public_topics AS (
    SELECT
        dashboard_topic AS topic_name,
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER() AS public_share
    FROM (
        SELECT
            CASE
                WHEN LOWER(title) REGEXP 'health|hospital|medical|disease|covid|doctor'
                    THEN 'Health'

                WHEN LOWER(title) REGEXP 'education|school|student|teacher|university'
                    THEN 'education'

                WHEN LOWER(title) REGEXP 'environment|climate|carbon|pollution|energy'
                    THEN 'environment'

                WHEN LOWER(title) REGEXP 'crime|police|security|violence|safety'
                    THEN 'safety'

                ELSE NULL
            END AS dashboard_topic
        FROM fact_reddit_posts
    ) x
    WHERE dashboard_topic IS NOT NULL
    GROUP BY dashboard_topic
),

government_topics AS (
    SELECT
        t.topic_name,
        AVG(g.value) * 100.0 /
        SUM(AVG(g.value)) OVER() AS government_share
    FROM fact_government_expenditure g
    JOIN dim_topics t
        ON g.topic_id = t.topic_id
    WHERE t.topic_name IN
    ('Health','education','environment','safety')
    GROUP BY t.topic_name
)

SELECT
    p.topic_name,
    ROUND(p.public_share,2) AS public_share,
    ROUND(g.government_share,2) AS government_share
FROM public_topics p
LEFT JOIN government_topics g
ON p.topic_name = g.topic_name;

-- =====================================================
-- QUERY 15: Priority Gap Analysis
-- =====================================================
-- Purpose:
-- Identify where public attention differs from
-- government spending priorities.
--
-- Positive Gap:
-- Public talks more than government spends.
--
-- Negative Gap:
-- Government spends more than public discusses.
--
-- Use:
-- Diverging Bar Chart
-- =====================================================

WITH public_topics AS (
    SELECT
        dashboard_topic AS topic_name,
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER() AS public_share
    FROM (
        SELECT
            CASE
                WHEN LOWER(title) REGEXP 'health|hospital|medical|disease|covid|doctor'
                    THEN 'Health'

                WHEN LOWER(title) REGEXP 'education|school|student|teacher|university'
                    THEN 'education'

                WHEN LOWER(title) REGEXP 'environment|climate|carbon|pollution|energy'
                    THEN 'environment'

                WHEN LOWER(title) REGEXP 'crime|police|security|violence|safety'
                    THEN 'safety'

                ELSE NULL
            END AS dashboard_topic
        FROM fact_reddit_posts
    ) x
    WHERE dashboard_topic IS NOT NULL
    GROUP BY dashboard_topic
),

government_topics AS (
    SELECT
        t.topic_name,
        AVG(g.value) * 100.0 /
        SUM(AVG(g.value)) OVER() AS government_share
    FROM fact_government_expenditure g
    JOIN dim_topics t
        ON g.topic_id = t.topic_id
    WHERE t.topic_name IN
    ('Health','education','environment','safety')
    GROUP BY t.topic_name
)

SELECT
    p.topic_name,
    ROUND(p.public_share,2) AS public_share,
    ROUND(g.government_share,2) AS government_share,
    ROUND(
        p.public_share - g.government_share,
        2
    ) AS priority_gap
FROM public_topics p
JOIN government_topics g
ON p.topic_name = g.topic_name
ORDER BY ABS(priority_gap) DESC;