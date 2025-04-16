# 📊 CSV SQL Studio

Treat your CSV files as tables, use select/update/delete/join with them using SQL.

![CSV SQL Studio](assets/CSV%20SQL%20Studio.png)

## Reason

I wanted to store tables in github and i come across [dolthub](https://www.dolthub.com/), which is great product, but I don't wanted use github or any other service, so built this tool to use CSV files as tables and do SQL operations on them.

other use cases,

- Analyze data in CSV files using SQL
- Use SQL to update data in CSV files
- Use SQL to join multiple CSV files

## Features

- all SQL operations supported
- import folder of CSV files as database
- publish changes to CSV files

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run main.py
```

## How to use

1. At left panel, first add connection by specifying the folder where CSV files are stored, and click on `Add Connection`.
2. Now select database from the dropdown, it will automatically load all CSV files in the folder as tables.
3. Now you can run any SQL query on the tables, perform any operation like select, update, delete, join, etc.
4. Once you are done with the changes, click on `Publish Changes` to save the changes to CSV files.

## How it works

Our main packages are [duckdb](https://pypi.org/project/duckdb/) and [streamlit](https://pypi.org/project/streamlit/).

1. First we create tables in duckdb using the CSV files in the folder.
2. Once we have the tables, we can run any SQL query on them using duckdb engine.
3. Once we are done with the changes, we can save the changes to CSV files using duckdb engine.
