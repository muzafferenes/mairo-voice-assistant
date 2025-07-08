import sqlite3

# Veritabanına bağlan
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Tabloyu oluştur
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    embedding_path TEXT,
    created_at DATETIME
)
""")

conn.commit()
conn.close()

print("Veritabanı oluşturuldu.")
