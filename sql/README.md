# SQL contents

`dashboard_queries.sql` contains the analytical queries behind the dashboard. Select your warehouse database before running it. It references the fact and dimension tables used by `app.py`.

`CREATE TABLE` statements, staging tables, and ETL/load scripts are not included. This SQL file is therefore **not** a database initializer. The warehouse must already exist and contain compatible tables and data before the dashboard APIs can return results. No database commands are run automatically.
