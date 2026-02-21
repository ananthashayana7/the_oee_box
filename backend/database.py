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

            # Seed default users if not exists
            users = [
                ("admin", "admin123", "admin"),
                ("engineer", "eng123", "engineer"),
                ("operator", "op123", "operator")
            ]

            for u, p, r in users:
                await cursor.execute("SELECT * FROM users WHERE username = ?", (u,))
                if not await cursor.fetchone():
                    logger.info(f"Seeding default user: {u}")
                    hashed_pw = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    await cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (u, hashed_pw, r))

            # Machine Config Table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS machine_config (
                    machine_id TEXT PRIMARY KEY,
                    ideal_cycle_time REAL,
                    shift_start_hour INTEGER,
                    target_availability REAL,
                    target_performance REAL,
                    target_quality REAL
                )
            """)

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

    async def cleanup_old_data(self, days=30):
        if not self.db: return
        retention_cutoff = time.time() - (days * 86400)
        await self.db.execute("DELETE FROM telemetry WHERE timestamp < ?", (retention_cutoff,))
        await self.db.execute("DELETE FROM audit_logs WHERE timestamp < ?", (retention_cutoff,))
        await self.db.execute("DELETE FROM alerts WHERE timestamp < ?", (retention_cutoff,))
        await self.db.commit()
        logger.info(f"Cleaned up data older than {days} days")

    async def get_audit_logs(self, limit=20):
        if not self.db: return []
        async with self.db.execute("SELECT id, timestamp, action, user, details FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [{"timestamp": row[1], "action": row[2], "user": row[3], "details": row[4]} for row in rows]

    # Machine Config Methods
    async def get_machine_config(self, machine_id):
        if not self.db: return None
        async with self.db.execute("SELECT * FROM machine_config WHERE machine_id = ?", (machine_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "machine_id": row[0],
                    "ideal_cycle_time": row[1],
                    "shift_start_hour": row[2],
                    "target_availability": row[3],
                    "target_performance": row[4],
                    "target_quality": row[5]
                }
        return None

    async def update_machine_config(self, machine_id, config):
        if not self.db: return
        # Upsert
        try:
            await self.db.execute("""
                INSERT INTO machine_config (machine_id, ideal_cycle_time, shift_start_hour, target_availability, target_performance, target_quality)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(machine_id) DO UPDATE SET
                    ideal_cycle_time=excluded.ideal_cycle_time,
                    shift_start_hour=excluded.shift_start_hour,
                    target_availability=excluded.target_availability,
                    target_performance=excluded.target_performance,
                    target_quality=excluded.target_quality
            """, (machine_id, config.ideal_cycle_time, config.shift_start_hour, config.target_availability, config.target_performance, config.target_quality))
            await self.db.commit()
        except Exception as e:
            logger.error(f"Config Update Failed: {e}")

db_manager = DatabaseManager()
