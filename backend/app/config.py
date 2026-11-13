import os

PORT = int(os.getenv("SALESCAST_PORT", "8000"))
DB_PATH = os.getenv("SALESCAST_DB_PATH", "backend/data/salescast.db")
