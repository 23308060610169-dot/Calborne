import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).with_name("calborne.db")

schema = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  nombre TEXT,
  paterno TEXT,
  materno TEXT,
  fecha_nacimiento TEXT,
  genero TEXT,
  telefono TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS perfiles_usuario (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  usuario_id INTEGER NOT NULL,
  altura_cm REAL,
  peso_actual_kg REAL,
  peso_objetivo_kg REAL,
  nivel_actividad TEXT,
  objetivo_salud TEXT,
  meta_semanal TEXT,
  condiciones_medicas TEXT,
  medicamentos TEXT,
  alergias_alimentarias TEXT,
  preferencias_alimentarias TEXT,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
"""

def main():
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        # habilitar foreign keys en SQLite
        cur.execute("PRAGMA foreign_keys = ON;")
        # ejecutar cada sentencia por separado
        for stmt in [s.strip() for s in schema.split(";") if s.strip()]:
            cur.execute(stmt)
        conn.commit()
        print(f"Base creada/actualizada en: {DB_FILE}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()