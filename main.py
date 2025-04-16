# app.py
import streamlit as st
import duckdb
import os
import glob
import pandas as pd
from pathlib import Path
from streamlit_extras.switch_page_button import switch_page
from streamlit_ace import st_ace

st.set_page_config(layout="wide")

# -------------------- State Management --------------------
if 'connections' not in st.session_state:
    if os.path.exists("connections.json"):
        import json
        with open("connections.json") as f:
            st.session_state.connections = {
                k: Path(v) for k, v in json.load(f).items()
            }
    else:
        st.session_state.connections = {}
if 'active_db' not in st.session_state:
    st.session_state.active_db = None
if 'duck_conns' not in st.session_state:
    st.session_state.duck_conns = {}
if 'notify' not in st.session_state:
    st.session_state.notify = ""

# -------------------- Helper Functions --------------------
def load_csv_tables(conn: duckdb.DuckDBPyConnection, db_path: Path):
    csv_files = glob.glob(str(db_path / '*.csv'))
    for csv in csv_files:
        table_name = Path(csv).stem
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS 
            SELECT * FROM read_csv_auto('{csv}', header=true, AUTO_DETECT=true)
        """)
    st.toast(f"{len(csv_files)} table(s) loaded from {db_path}", icon="📄")

def publish_changes(conn: duckdb.DuckDBPyConnection, db_path: Path):
    tables = conn.execute("SHOW TABLES").fetchdf()['name'].tolist()
    for table_name in tables:
        try:
            output_path = db_path / f"{table_name}.csv"
            conn.execute(f"COPY {table_name} TO '{output_path}' (HEADER, DELIMITER ',')")
        except Exception as e:
            st.toast(f"Failed to publish {table_name}: {e}", icon="⚠️")
    st.toast("All changes published to CSV", icon="✅")

def sync_tables(conn: duckdb.DuckDBPyConnection, db_path: Path):
    tables = conn.execute("SHOW TABLES").fetchdf()['name'].tolist()
    for table_name in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    load_csv_tables(conn, db_path)
    st.toast("Tables loaded from folder", icon="🔁")

def run_query(conn: duckdb.DuckDBPyConnection, query: str):
    try:
        result = conn.execute(query).fetchdf()
        return result.dropna(how="all"), None
    except Exception as e:
        return None, str(e)

# -------------------- Sidebar: Connection --------------------
st.sidebar.title("Database Connections")
dbname = st.sidebar.text_input("DB Name")
dbpath = st.sidebar.text_input("Folder Path")
if st.sidebar.button("Add Connection"):
    if dbname and dbpath and os.path.isdir(dbpath):
        conn = duckdb.connect()
        path_obj = Path(dbpath)
        load_csv_tables(conn, path_obj)
        st.session_state.connections[dbname] = path_obj
        st.session_state.duck_conns[dbname] = conn
        with open("connections.json", "w") as f:
            import json
            json.dump({k: str(v) for k, v in st.session_state.connections.items()}, f)
        st.toast(f"Database '{dbname}' added ✅")
    else:
        st.sidebar.warning("Invalid DB name or path")

selected_db = st.sidebar.selectbox("Select Database", list(st.session_state.connections.keys()))
if selected_db:
    st.session_state.active_db = selected_db
    if selected_db not in st.session_state.duck_conns:
        conn = duckdb.connect()
        load_csv_tables(conn, st.session_state.connections[selected_db])
        st.session_state.duck_conns[selected_db] = conn
    active_conn = st.session_state.duck_conns[selected_db]
    active_path = st.session_state.connections[selected_db]
    st.sidebar.markdown("### Actions")
    col1, col2 = st.sidebar.columns(2)
    if col1.button("🔁 Load"):
        sync_tables(active_conn, active_path)
    if col2.button("📤 Publish"):
        publish_changes(active_conn, active_path)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Tables")
    tables = active_conn.execute("SHOW TABLES").fetchall()
    for (table_name,) in tables:
        if st.sidebar.button(f"📄 {table_name}"):
            st.session_state.selected_table = table_name
else:
    active_conn = None
    active_path = None

# -------------------- Main Layout --------------------
st.title("📊 CSV SQL Studio")

if active_conn:
    if 'selected_table' in st.session_state:
        with st.container():
            c1, c2 = st.columns([0.95, 0.05])
            with c1:
                st.subheader(f"Schema for table: {st.session_state.selected_table}")
            with c2:
                if st.button("❌", key="close_schema"):
                    del st.session_state.selected_table
        schema = active_conn.execute(f"PRAGMA table_info({st.session_state.selected_table})").fetchdf()
        st.dataframe(schema, use_container_width=True)

    sql_code = st_ace(language="sql", height=250, key="sql_editor", auto_update=True)

    # Store query results in session state to persist them
    if "query_result" not in st.session_state:
        st.session_state.query_result = None
    if "query_error" not in st.session_state:
        st.session_state.query_error = None

    if st.button("▶️ Run Query"):
        if sql_code.strip():
            result, error = run_query(active_conn, sql_code.strip())
            st.session_state.query_result = result
            st.session_state.query_error = error
        else:
            st.warning("Please enter a SQL query to run.")

    # Display query results or errors
    if st.session_state.query_error:
        st.error(st.session_state.query_error)
    elif st.session_state.query_result is not None:
        if st.session_state.query_result.empty:
            st.toast("Query executed. No rows returned.", icon="ℹ️")
        else:
            st.subheader("Result")
            st.dataframe(
                st.session_state.query_result,
                use_container_width=True,
                height=min(500, 40 + 30 * len(st.session_state.query_result))
            )
