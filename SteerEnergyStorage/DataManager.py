import sqlite3 as sql
import pandas as pd
import numpy as np

H_TO_S = 3600
mA_TO_A = 1e-3
G_TO_KG = 1e-3

class DataManager:
    
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._connection = sql.connect(db_path)
        self._cursor = self._connection.cursor()

    def create_table(self, table_name: str, columns: dict):
        """
        Function to create a table in the database.

        :param table_name: Name of the table.
        :param columns: Dictionary of columns and their types.
        """
        columns_str = ', '.join([f'{k} {v}' for k, v in columns.items()])
        self._cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})')
        self._connection.commit()

    def drop_table(self, table_name: str):
        """
        Function to drop a table from the database.

        :param table_name: Name of the table.
        """
        self._cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
        self._connection.commit()

    def get_table_names(self):
        """
        Function to get the names of all tables in the database.

        :return: List of table names.
        """
        self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in self._cursor.fetchall()]

    def insert_data(self, table_name: str, data: pd.DataFrame):
        """
        Inserts data into the database only if it doesn’t already exist.

        :param table_name: Name of the table.
        :param data: DataFrame containing the data to insert.
        """
        for _, row in data.iterrows():
            conditions = ' AND '.join([f"{col} = ?" for col in data.columns])
            check_query = f"SELECT COUNT(*) FROM {table_name} WHERE {conditions}"
            
            self._cursor.execute(check_query, tuple(row))
            if self._cursor.fetchone()[0] == 0:  # If the row does not exist, insert it
                insert_query = f"INSERT INTO {table_name} ({', '.join(data.columns)}) VALUES ({', '.join(['?'] * len(row))})"
                self._cursor.execute(insert_query, tuple(row))

        self._connection.commit()

    def get_data(self, table_name: str, columns: list = None, condition: str | list[str] = None, latest_column: str = None):
        """
        Retrieve data from the database.

        :param table_name: Name of the table.
        :param columns: List of columns to retrieve. If None, retrieves all columns.
        :param condition: Optional condition (single string or list of conditions).
        :param latest_column: Column name to find the most recent row.
        """
        # If columns is not provided, get all columns from the table
        if columns is None:
            self._cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = self._cursor.fetchall()
            columns = [col[1] for col in columns_info]  # Extract column names
            if not columns:
                raise ValueError(f"Table '{table_name}' does not exist or has no columns.")

        columns_str = ', '.join(columns)
        query = f"SELECT {columns_str} FROM {table_name}"

        # Add condition if specified
        if condition:
            if isinstance(condition, list):
                condition_str = ' AND '.join(condition)
            else:
                condition_str = condition
            query += f" WHERE {condition_str}"

        # If latest_column is provided, get the most recent entry
        if latest_column:
            query += f" ORDER BY {latest_column} DESC LIMIT 1"

        # Execute and return the result
        self._cursor.execute(query)
        data = self._cursor.fetchall()
        
        return pd.DataFrame(data, columns=columns)
    
    def get_unique_values(self, table_name: str, column_name: str):
        """
        Retrieves all unique values from a specified column.
        
        :param table_name: The name of the table.
        :param column_name: The column to retrieve unique values from.
        :return: A list of unique values.
        """
        query = f"SELECT DISTINCT {column_name} FROM {table_name}"
        self._cursor.execute(query)
        return [row[0] for row in self._cursor.fetchall()]
    
    @staticmethod
    def read_half_cell_curve(half_cell_path) -> pd.DataFrame:
        """
        Function to read in a half cell curve for this active material

        :param half_cell_path: Path to the half cell data file.
        :return: DataFrame with the specific capacity and voltage.
        """
        try:
            data = pd.read_csv(half_cell_path)
        except:
            raise FileNotFoundError(f"Could not find the file at {half_cell_path}")
        
        if 'Specific Capacity (mAh/g)' not in data.columns:
            raise ValueError("The file must have a column named 'Specific Capacity (mAh/g)'")
        
        if 'Voltage (V)' not in data.columns:
            raise ValueError("The file must have a column named 'Voltage (V)'")
        
        if 'Step_ID' not in data.columns:
            raise ValueError("The file must have a column named 'Step_ID'")
        
        data = (data
                .rename(columns={'Specific Capacity (mAh/g)': 'specific_capacity', 'Voltage (V)': 'voltage', 'Step_ID': 'step_id'})
                .assign(specific_capacity=lambda x: x['specific_capacity'] * (H_TO_S * mA_TO_A / G_TO_KG))
                .filter(['specific_capacity', 'voltage', 'step_id'])
                .groupby(['specific_capacity', 'step_id'], group_keys=False)['voltage'].max()
                .reset_index()
                .sort_values(['step_id', 'specific_capacity'])
                )

        return data
    
    def remove_data(self, table_name: str, condition: str):
        """
        Function to remove data from the database.

        :param table_name: Name of the table.
        :param condition: Condition to remove rows.
        """
        self._cursor.execute(f"DELETE FROM {table_name} WHERE {condition}")
        self._connection.commit()
        
    def __del__(self):
        self._connection.close()
