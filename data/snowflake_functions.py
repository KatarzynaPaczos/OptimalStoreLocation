import os
import pandas as pd
import logging
import snowflake.connector
from typing import Optional
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas
from data.utils import fetch_stores_data, fetch_housing_data
from data.utils import DEFAULT_LEVELS, DEFAULT_AREA

load_dotenv()
logger = logging.getLogger(__name__)


def get_connection_snowflake():
    """Establish connection to Snowflake if credentials are available."""
    try:
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT")
        )
        logger.info(f"Sucessfully connected to Snowflake as user {os.getenv('SNOWFLAKE_USER')}")

        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        database = os.getenv("SNOWFLAKE_DATABASE")
        cur = conn.cursor()
        cur.execute(f"""
            CREATE WAREHOUSE IF NOT EXISTS {warehouse} WITH WAREHOUSE_SIZE = 'XSMALL'
            AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;
            """
        )
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
        cur.execute(f"USE WAREHOUSE {warehouse}")
        cur.execute(f"USE DATABASE {database}")
        logger.info(
            f"Connected to Snowflake. Environment ready: {warehouse} / {database}"
        )
        cur.close()
        return conn
    except Exception as e:
        logger.warning(f"Could not connect to Snowflake: {e}. Will proceed in local mode.")
        return None


def read_table(conn, schema: str, table: str) -> Optional[pd.DataFrame]:
    """Return True if table exists and can be read, False otherwise."""
    try:
        cur = conn.cursor()
        query = f"SELECT * FROM {schema}.{table}"
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=columns)
        cur.close()
        logger.info(f"Retrieved {len(df)} rows from {schema}.{table}")
        return df
    except Exception as e:
        logger.warning(e)
        return None


def ensure_schema_exists(conn, schema: str):
    """Check if schema exists; if not, create it."""
    cur = conn.cursor()
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    logger.info(f"Verified schema: {schema} (created if missing)")
    cur.close()


def run_etl_snowflake_stores(conn, city: str, country: str, store: str, schema: str):
    stores = fetch_stores_data(city, country, store)
    upload_to_snowflake(conn, stores, schema, "L1_RAW")
    transform_stores_silver(conn, schema, "L1_RAW", "L2_CLEANED")
    transform_stores_golden(conn, schema, "L2_CLEANED", "L3_GOLDEN")
    return read_table(conn, schema, "L3_GOLDEN")


def run_etl_snowflake_housing(conn, city: str, country: str, schema: str):
    housing = fetch_housing_data(city, country)
    upload_to_snowflake(conn, housing, schema, "L1_RAW")
    transform_housing_silver(conn, schema, "L1_RAW", "L2_CLEANED")
    transform_housing_golden(conn, schema, "L2_CLEANED", "L3_GOLDEN")
    return read_table(conn, schema, "L3_GOLDEN")


def upload_to_snowflake(conn, df: pd.DataFrame, schema: str, table: str):
    ensure_schema_exists(conn, schema)
    success, _, nrows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name=table,
        schema=schema,
        overwrite=True
    )
    logger.info(f"Uploaded {nrows} rows to {schema}.{table} (success={success})")
    return success


def transform_stores_silver(conn, schema: str, table_old: str, table_new: str):
    cur = conn.cursor()
    logger.info("Transforming L1_RAW → L2_CLEANED")
    cur.execute(f"""
        CREATE OR REPLACE TABLE {schema}.{table_new} AS
        SELECT *
        FROM {schema}.{table_old}
        WHERE 'lat' IS NOT NULL AND 'lon' IS NOT NULL
    """)
    cur.close()


def transform_stores_golden(conn, schema: str, table_old: str, table_new: str):
    cur = conn.cursor()
    logger.info("Transforming L2_CLEANED → L3_GOLDEN")

    cur.execute(f"""
        CREATE OR REPLACE TABLE {schema}.{table_new} CLONE {schema}.{table_old};
    """)
    cur.close()


def transform_housing_silver(conn, schema: str, table_old: str, table_new: str):
    cur = conn.cursor()


    logger.info("Transforming HOUSING L1_RAW → L2_CLEANED")

    query = f"""
    CREATE OR REPLACE TABLE {schema}.{table_new} AS
    SELECT
        "housenumber",
        "street",
        "building_type",
        COALESCE("lat", 0) AS "lat",
        COALESCE("lon", 0) AS "lon",
        /* Replace NULL or zero area_m2 with default */
        CASE
            WHEN "area_m2" IS NULL OR "area_m2" = 0 THEN {DEFAULT_AREA}
            ELSE "area_m2"
        END AS "area_m2",
        /* Convert and fill levels */
        CASE
            WHEN TRY_TO_NUMBER("levels") IS NULL OR TRY_TO_NUMBER("levels") = 0 THEN {DEFAULT_LEVELS}
            ELSE TRY_TO_NUMBER("levels")
        END AS "levels"
    FROM {schema}.{table_old}
    WHERE "lat" IS NOT NULL AND "lon" IS NOT NULL;
    """
    cur.execute(query)
    cur.close()
    logger.info(f"Created {schema}.{table_new}")


def transform_housing_golden(conn, schema: str, table_old: str, table_new: str):
    cur = conn.cursor()
    logger.info("Transforming HOUSING L2_CLEANED → L3_GOLDEN")

    query = f"""
    CREATE OR REPLACE TABLE {schema}.{table_new} AS
    SELECT
        *,
        /* Example heuristic: residents = area_m2 * levels / 30 */
        ("area_m2" * "levels") / 30 AS "residents"
    FROM {schema}.{table_old};
    """.strip()

    cur.execute(query)
    cur.close()
    logger.info(f"Created {schema}.{table_new}")
