import sqlite3

# Crear conexión a la base de datos SQLite3
conn = sqlite3.connect("bingo2.db")
cursor = conn.cursor()

# Tabla "partida" (solo permite una fila)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS partida (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Solo una fila, siempre tendrá id = 1
    partida TEXT,
    precio_de_carton REAL,
    precio_dolar REAL,
    zelle TEXT,
    estatus TEXT,
    modalidad_carton_regalo TEXT,
    recompensa REAL,
    imagen TEXT,
    total_cartones INTEGER DEFAULT 200
               );
""")

# Tabla "cartones_disponibles" (del 1 al 1500)
cursor.execute("""
CREATE TABLE IF NOT EXISTS cartones_disponibles (
    carton_disponible INTEGER PRIMARY KEY
);""")

# Insertar los cartones disponibles (1 al 1500)
cursor.executemany("""
INSERT OR IGNORE INTO cartones_disponibles (carton_disponible) VALUES (?);
""", [(i,) for i in range(1, 201)])

# Tabla "cartones_usados"
cursor.execute("""
CREATE TABLE IF NOT EXISTS cartones_usados (
    carton INTEGER PRIMARY KEY);
""")

# Tabla "requeridos"
cursor.execute("""
CREATE TABLE IF NOT EXISTS requeridos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_apellidos TEXT NOT NULL,
    cedula TEXT NOT NULL,
    telefono TEXT NOT NULL,
    referencia TEXT NOT NULL,
    cartones_solicitados INTEGER NOT NULL,
    monto TEXT NOT NULL,
    fecha TEXT NOT NULL,
    estatus TEXT DEFAULT NULL,
    link TEXT
);
""")

# Insertar una fila inicial con valores por defecto si no hay registros
cursor.execute("""
            INSERT INTO partida (partida, recompensa, precio_de_carton, modalidad_carton_regalo, estatus, imagen, total_cartones)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, ("", "", 0.0, "", "Venta finalizada", "logo.png", 200))
conn.commit()

# Confirmar los cambios y cerrar la conexión

conn.close()

print("Base de datos creada con éxito.")
