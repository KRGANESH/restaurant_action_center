import sqlite3

from config import DATABASE_BACKEND, DB_PATH


def get_database_client():
    if DATABASE_BACKEND == "sqlite":
        return sqlite3.connect(DB_PATH)

    if DATABASE_BACKEND == "bigquery":
        raise NotImplementedError(
            "BigQuery client is not configured yet. Add a BigQuery adapter here."
        )

    raise ValueError(f"Unsupported database backend: {DATABASE_BACKEND}")
