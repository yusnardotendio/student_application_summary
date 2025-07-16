import sqlite3
import pandas as pd

class EvaluationResultDB:
    def __init__(self, db_path='evaluation_results.db'):
        self.db_path = db_path
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self._connect() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS evaluation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    markdown TEXT NOT NULL,
                    created_at TEXT,
                    decision TEXT
                )
            ''')

    def add_result(self, name, markdown, created_at, decision):
        with self._connect() as conn:
            conn.execute(
                'INSERT INTO evaluation_results (name, markdown, created_at, decision) VALUES (?, ?, ?, ?)',
                (name, markdown, created_at, decision)
            )

    def get_result(self, result_id):
        with self._connect() as conn:
            cur = conn.execute(
                'SELECT id, created_at, name, decision, markdown FROM evaluation_results WHERE id = ?',
                (result_id,)
            )
            return cur.fetchone()

    def get_all_results(self):
        with self._connect() as conn:
            cur = conn.execute('SELECT id, created_at, name, decision, markdown FROM evaluation_results ORDER BY id')
            return cur.fetchall()

    def update_result(self, result_id, name, markdown):
        with self._connect() as conn:
            conn.execute(
                'UPDATE evaluation_results SET name = ?, markdown = ? WHERE id = ?',
                (name, markdown, result_id)
            )

    def delete_result(self, result_id):
        with self._connect() as conn:
            conn.execute(
                'DELETE FROM evaluation_results WHERE id = ?',
                (result_id,)
            )

    def get_dataframe(self) -> pd.DataFrame:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, created_at, decision FROM evaluation_results ORDER BY id")
            rows = cursor.fetchall()
            df = pd.DataFrame(rows, columns=["ID", "Applicant Name", "Created At", "Decision"])

            return df
        
     