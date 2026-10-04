"""CashSight SQLite Storage & Persistence Layer.

Provides data access boundaries, user isolation, consent management,
trial tracking, and complete data deletion.
Follows docs/ARCHITECTURE.md section 5.10, docs/PRD.md FR-012/FR-013, and docs/SECURITY.md.

SECURITY CONSTRAINTS:
- All SQL statements use parameterized queries to prevent SQL injection.
- Bank login credentials are never stored.
- Supports complete user data deletion on consent revocation or request.
"""

from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import sqlite3
import pandas as pd

from config import (
    DEFAULT_DB_PATH,
    FREE_TRIAL_DAYS,
    DEFAULT_SAFETY_CUSHION,
)


class DatabaseManager:
    """Encapsulates SQLite operations with parameterized queries and transaction safety."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Opens a SQLite connection with row factories enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self) -> None:
        """Creates the approved database schema if not already initialized."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Users table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                business_name TEXT NOT NULL,
                business_type TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                safety_cushion REAL DEFAULT 25000.0,
                current_balance REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                trial_ends_at TEXT NOT NULL,
                subscription_status TEXT DEFAULT 'trial_active'
            );
            """)

            # 2. Consents table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS consents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                data_period_days INTEGER DEFAULT 180,
                status TEXT NOT NULL,
                granted_at TEXT NOT NULL,
                revoked_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """)

            # 3. Transactions table (Normalized common schema)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                source TEXT DEFAULT 'csv',
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
            """)

            # Indexes for efficient date and user filtering
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_user ON transactions(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_consent_user ON consents(user_id);")
            conn.commit()

    def save_user(self, user_data: Dict[str, Any]) -> str:
        """Creates or updates a user profile and initializes the 30-day trial."""
        now = datetime.now()
        trial_end = now + timedelta(days=FREE_TRIAL_DAYS)
        user_id = user_data.get("id") or f"user_{int(now.timestamp())}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (
                id, name, phone, business_name, business_type, language,
                safety_cushion, current_balance, created_at, trial_ends_at, subscription_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                phone=excluded.phone,
                business_name=excluded.business_name,
                business_type=excluded.business_type,
                language=excluded.language,
                safety_cushion=excluded.safety_cushion,
                current_balance=excluded.current_balance;
            """, (
                user_id,
                user_data.get("name", "").strip(),
                user_data.get("phone", "").strip(),
                user_data.get("business_name", "").strip(),
                user_data.get("business_type", "").strip(),
                user_data.get("language", "en"),
                float(user_data.get("safety_cushion", DEFAULT_SAFETY_CUSHION)),
                float(user_data.get("current_balance", 0.0)),
                now.isoformat(),
                trial_end.isoformat(),
                "trial_active",
            ))
            conn.commit()
        return user_id

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves user profile by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_user_balance(self, user_id: str, current_balance: float) -> None:
        """Updates user's current verified cash balance."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET current_balance = ? WHERE id = ?;",
                (float(current_balance), user_id)
            )
            conn.commit()

    def update_safety_cushion(self, user_id: str, cushion: float) -> None:
        """Updates user's configured safety cushion."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET safety_cushion = ? WHERE id = ?;",
                (float(cushion), user_id)
            )
            conn.commit()

    def record_consent(
        self,
        user_id: str,
        provider: str,
        data_period_days: int = 180,
    ) -> str:
        """Records an explicit consent entry for financial data access."""
        consent_id = f"c_{user_id}_{int(datetime.now().timestamp())}"
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute("""
            INSERT INTO consents (id, user_id, provider, data_period_days, status, granted_at)
            VALUES (?, ?, ?, ?, 'ACTIVE', ?);
            """, (consent_id, user_id, provider, data_period_days, now_str))
            conn.commit()
        return consent_id

    def revoke_consent(self, user_id: str, consent_id: Optional[str] = None) -> bool:
        """Revokes consent for the user."""
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            if consent_id:
                conn.execute(
                    "UPDATE consents SET status = 'REVOKED', revoked_at = ? WHERE id = ? AND user_id = ?;",
                    (now_str, consent_id, user_id)
                )
            else:
                conn.execute(
                    "UPDATE consents SET status = 'REVOKED', revoked_at = ? WHERE user_id = ? AND status = 'ACTIVE';",
                    (now_str, user_id)
                )
            conn.commit()
            return True

    def has_active_consent(self, user_id: str, provider: Optional[str] = None) -> bool:
        """Checks if user has an active, non-revoked consent."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if provider:
                cursor.execute(
                    "SELECT 1 FROM consents WHERE user_id = ? AND provider = ? AND status = 'ACTIVE' LIMIT 1;",
                    (user_id, provider)
                )
            else:
                cursor.execute(
                    "SELECT 1 FROM consents WHERE user_id = ? AND status = 'ACTIVE' LIMIT 1;",
                    (user_id,)
                )
            return cursor.fetchone() is not None

    def save_transactions(
        self,
        user_id: str,
        df_transactions: pd.DataFrame,
        source: str = "csv",
        replace_existing: bool = True,
    ) -> int:
        """Stores canonical transactions for a user."""
        if df_transactions.empty:
            return 0

        now_str = datetime.now().isoformat()
        rows = []
        for _, row in df_transactions.iterrows():
            rows.append((
                user_id,
                str(row["date"])[:10],
                str(row["description"]),
                str(row["category"]),
                str(row["type"]),
                float(row["amount"]),
                source,
                now_str,
            ))

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if replace_existing:
                cursor.execute("DELETE FROM transactions WHERE user_id = ?;", (user_id,))

            cursor.executemany("""
            INSERT INTO transactions (user_id, date, description, category, type, amount, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, rows)
            conn.commit()
            return len(rows)

    def get_transactions(self, user_id: str) -> pd.DataFrame:
        """Retrieves all canonical transactions for a user sorted chronologically."""
        with self.get_connection() as conn:
            query = """
            SELECT date, description, category, type, amount, source
            FROM transactions
            WHERE user_id = ?
            ORDER BY date ASC, id ASC;
            """
            df = pd.read_sql_query(query, conn, params=(user_id,))
            return df

    def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Permanently deletes all data associated with a user (Right to Erasure / FR-013)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE user_id = ?;", (user_id,))
            txns_deleted = cursor.rowcount
            cursor.execute("DELETE FROM consents WHERE user_id = ?;", (user_id,))
            consents_deleted = cursor.rowcount
            cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
            users_deleted = cursor.rowcount
            conn.commit()

        return {
            "user_id": user_id,
            "success": True,
            "deleted": {
                "users": users_deleted,
                "transactions": txns_deleted,
                "consents": consents_deleted,
            },
            "timestamp": datetime.now().isoformat(),
        }

    def get_trial_status(self, user_id: str) -> Dict[str, Any]:
        """Calculates 30-day free trial state and remaining days."""
        user = self.get_user(user_id)
        if not user:
            return {"is_valid_user": False}

        now = datetime.now()
        import math
        trial_ends_dt = datetime.fromisoformat(user["trial_ends_at"])
        remaining_seconds = (trial_ends_dt - now).total_seconds()
        remaining_days = max(0, int(math.ceil(remaining_seconds / 86400.0)))
        is_expired = now > trial_ends_dt

        return {
            "is_valid_user": True,
            "user_id": user_id,
            "subscription_status": user.get("subscription_status", "trial_active"),
            "trial_ends_at": user["trial_ends_at"][:10],
            "days_remaining": remaining_days,
            "is_trial_expired": is_expired,
            "plan_type": "30-Day Free Trial" if not is_expired else "Trial Expired (Paid Plan Required)",
        }


# Global storage instance
db = DatabaseManager()
