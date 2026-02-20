import aiosqlite
import logging
import asyncio
import time
import bcrypt

logger = logging.getLogger("database")

class DatabaseManager:
    def __init__(self, db_path="oee_data.db"):
        self.db_path = db_path
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path)
        await self.init_tables()
        logger.info(f"Connected to database: {self.db_path}")

    async def close(self):
        if self.db:
            await self.db.close()
            logger.info("Closed database connection")

    async def init_tables(self):
        async with self.db.cursor() as cursor:
            # Telemetry Table (Time Series)
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    machine_id TEXT,
                    key TEXT,
                    value REAL
                )
            """)
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry (timestamp)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_machine ON telemetry (machine_id)")

            # Users Table (Auth)
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT,
                    role TEXT
                )
            """)

            # Audit Logs (AI Shadow Mode & User Actions)
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    action TEXT,
                    user TEXT,
                    details TEXT,
                    signature TEXT
                )
            """)

            # Alerts (Resilience)
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    message TEXT,
                    severity TEXT,
                    resolved BOOLEAN DEFAULT 0
                )
            """)

            # Seed default admin user if not exists
            await cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            if not await cursor.fetchone():
                logger.info("Seeding default admin user")
                hashed_pw = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                await cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", hashed_pw, "admin"))

            await self.db.commit()

    async def insert_telemetry(self, timestamp, machine_id, key, value):
        if not self.db: return
        try:
            # Only store numeric values for charting
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                 await self.db.execute("INSERT INTO telemetry (timestamp, machine_id, key, value) VALUES (?, ?, ?, ?)", (timestamp, machine_id, key, value))
                 await self.db.commit()
        except Exception as e:
            logger.error(f"DB Write Error: {e}")

    async def get_telemetry_history(self, machine_id, key, limit=60):
        if not self.db: return []
        async with self.db.execute("SELECT timestamp, value FROM telemetry WHERE machine_id = ? AND key = ? ORDER BY timestamp DESC LIMIT ?", (machine_id, key, limit)) as cursor:
            rows = await cursor.fetchall()
            # Convert to list of dicts and reverse (oldest first)
            return [{"timestamp": row[0], key: row[1]} for row in rows][::-1]

    async def log_audit(self, action, user, details="", signature=None):
        if not self.db: return
        await self.db.execute("INSERT INTO audit_logs (timestamp, action, user, details, signature) VALUES (?, ?, ?, ?, ?)", (time.time(), action, user, details, signature))
        await self.db.commit()

    async def create_alert(self, message, severity="info"):
        if not self.db: return
        await self.db.execute("INSERT INTO alerts (timestamp, message, severity) VALUES (?, ?, ?)", (time.time(), message, severity))
        await self.db.commit()

    async def get_active_alerts(self):
        if not self.db: return []
        async with self.db.execute("SELECT id, timestamp, message, severity FROM alerts WHERE resolved = 0 ORDER BY timestamp DESC LIMIT 10") as cursor:
            rows = await cursor.fetchall()
            return [{"id": row[0], "timestamp": row[1], "message": row[2], "severity": row[3]} for row in rows]

    async def get_audit_logs(self, limit=20):
        if not self.db: return []
        async with self.db.execute("SELECT id, timestamp, action, user, details FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [{"timestamp": row[1], "action": row[2], "user": row[3], "details": row[4]} for row in rows]

db_manager = DatabaseManager()
