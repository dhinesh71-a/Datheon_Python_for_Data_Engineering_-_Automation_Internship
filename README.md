# Datheon Python for Data Engineering & Automation Internship

This repository contains my completed projects for the Datheon Python for Data Engineering & Automation Internship.

## Tasks Completed

### Task 1: Web Scraper
- Extracts book information from a website.
- Saves scraped data in CSV and JSON formats.

### Task 2: Automated Data Cleaning & Schema Transformation
- Handles missing and invalid values.
- Removes duplicate records.
- Validates the data schema.
- Generates cleaning reports and logs.

### Task 3: Relational Database Auto-Ingestion & Upsert Engine
- Uses SQLite for database storage.
- Performs bulk data ingestion and upserts.
- Handles transactions and duplicate primary keys.
- Generates verification reports and logs.

### Task 4: Scheduled End-to-End ETL Pipeline with Alerting
- Runs the web scraper as the extraction stage.
- Transforms and validates the extracted book data.
- Loads records into SQLite using upsert operations.
- Generates pipeline logs and execution reports.
- Supports scheduled execution and optional email alerts.

## Technologies Used
- Python
- Pandas
- SQLite
- BeautifulSoup
- Requests
- Schedule

## Project Structure
- Task_1_Web_Scraper/
- Task_2_Data_Cleaning/
- Task_3_SQLite_Ingestion/
- Task_4_Scheduled_ETL_Pipeline/

## Verification
Task 4 successfully processed 1,000 book records. A second execution confirmed that the database still contained 1,000 records.

---
Developed as part of the Datheon Python for Data Engineering & Automation Internship.
