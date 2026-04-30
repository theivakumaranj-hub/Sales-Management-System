<img width="1846" height="777" alt="image" src="https://github.com/user-attachments/assets/ca2d0ca3-54cf-4e66-807a-49bbd98fc173" /># Sales-Management-System
A Branch-Based Sales Management System built with Python, utilizing Streamlit for the UI, Pandas for data manipulation, and Psycopg2 for PostgreSQL database integration.

# Branch-Based Sales Management System

## Project Overview
This is a data-driven web application built to manage branch sales, track payment splits, and analyze performance metrics. It features a role-based access system (Super Admin vs. Branch Admin) and uses a PostgreSQL backend for secure data storage and automated financial calculations.

## Tech Stack
* **Frontend:** Python (Streamlit)
* **Data Manipulation:** Pandas
* **Database:** PostgreSQL
* **Database Connector:** psycopg2

## Repository Contents
* `app.py`: The main Python script containing the Streamlit user interface and backend logic.
* `schema1.sql`: The database blueprint, including table structures, foreign keys, and the PL/pgSQL triggers used for automated payment tracking.
* `requirements.txt`: The list of required Python libraries.
* `*.csv`: The original raw datasets used to populate the initial database.

## How to Run This Application
1. **Set up the Database:** Open pgAdmin, create a new database, and run the code inside `schema1.sql` to build the tables and triggers.
2. **Install Dependencies:** Open your terminal and run:
   ```bash
   pip install -r requirements.txt

## Launch the App: In the terminal, run the following command to start the Streamlit server:
 ```bash
   streamlit run app.py
