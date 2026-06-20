import sqlite3

def actualizar_tabla(database_name):
    """
    Conecta a una base de datos SQLite y ejecuta una consulta SQL para
    añadir la columna 'session_id' a la tabla 'cartones_temporales'.
    """
    try:
        # Conectarse a la base de datos
        conn = sqlite3.connect(database_name)
        cursor = conn.cursor()

        # Consulta SQL para añadir la nueva columna
        consulta_sql = "ALTER TABLE cartones_temporales ADD COLUMN session_id TEXT;"

        # Ejecutar la consulta
        cursor.execute(consulta_sql)

        # Confirmar los cambios
        conn.commit()
        print(f"Columna 'session_id' agregada a la tabla 'cartones_temporales' en la base de datos {database_name} exitosamente.")

    except sqlite3.Error as e:
        print(f"Ocurrió un error al procesar la base de datos {database_name}: {e}")
    finally:
        # Cerrar la conexión
        if conn:
            conn.close()

# Bases de datos a procesar
databases = ['bingo.db', 'bingo2.db']

# Iterar sobre la lista y ejecutar la función para cada base de datos
for db in databases:
    actualizar_tabla(db)