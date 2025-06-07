from abc import ABC, abstractmethod
import sqlite3
import os
import pandas as pd


class AbstractDatabaseAdapter(ABC):
    @abstractmethod
    def save_dataframe(self, df: pd.DataFrame, table_name: str):
        pass

    @abstractmethod
    def load_dataframe(self, table_name: str) -> pd.DataFrame:
        pass


class SQLiteDatabaseAdapter(AbstractDatabaseAdapter):
    def __init__(self, db_path: str = "data/stock_data.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def save_dataframe(self, df: pd.DataFrame, table_name: str):
        with self._connect() as conn:
            df.to_sql(table_name, conn, if_exists='replace', index=False)

    def load_dataframe(self, table_name: str) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql(f"SELECT * FROM {table_name}", conn)


class DatabaseManager:
    def __init__(self, adapter: AbstractDatabaseAdapter):
        self.adapter = adapter

    def save_data(self, df: pd.DataFrame, table_name: str):
        print(f"Saving data to table '{table_name}'...")
        self.adapter.save_dataframe(df, table_name)
        print("✅ Data saved successfully.")

    def load_data(self, table_name: str) -> pd.DataFrame:
        print(f"Loading data from table '{table_name}'...")
        df = self.adapter.load_dataframe(table_name)
        print("✅ Data loaded successfully.")
        return df


# Example usage:
if __name__ == "__main__":
    sqlite_adapter = SQLiteDatabaseAdapter()
    db_manager = DatabaseManager(sqlite_adapter)

    sample_df = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})
    db_manager.save_data(sample_df, "test_table")
    loaded_df = db_manager.load_data("test_table")
    print(loaded_df)
