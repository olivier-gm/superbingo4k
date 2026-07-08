import sqlite3
import json
import time
import ast # Módulo más seguro que eval()

DB_NAME = "bingo.db"

def execute_query(query, params=(), fetch=False, fetchone=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        data = cursor.fetchall() if not fetchone else cursor.fetchone()
    else:
        conn.commit()
        data = None
    conn.close()
    return data



def obtener_comprador_por_cedula(cedula):
    """
    Recupera el nombre y los cartones vendidos de dos bases de datos usando la cédula.
    Retorna un diccionario con los datos estructurados para ambas partidas.
    """
        # --- Conexión a la primera base de datos (bingo.db) ---
    with sqlite3.connect("bingo.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT partida
            FROM partida
            WHERE 1 = 1''')
        partida1_titulo = cursor.fetchone()

    with sqlite3.connect("bingo2.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT partida
            FROM partida
            WHERE 1 = 1''')
        partida2_titulo = cursor.fetchone()
    partida1_titulo = partida1_titulo[0] if partida1_titulo else "Partida 1"  # Título para la primera partida
    partida2_titulo = partida2_titulo[0] if partida2_titulo else "Partida 2"  # Título para la segunda partida
    # Títulos para cada partida que se mostrarán en el HTML

    # --- Conexión a la primera base de datos (bingo.db) ---
    with sqlite3.connect("bingo.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT nombre_apellidos, cartones_solicitados
            FROM requeridos
            WHERE cedula = ?''', (cedula,))
        resultados = cursor.fetchall()

    # --- Conexión a la segunda base de datos (bingo2.db) ---
    with sqlite3.connect("bingo2.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cartones_solicitados
            FROM requeridos
            WHERE cedula = ?''', (cedula,))
        resultados2 = cursor.fetchall()

    # Si no se encuentran datos en ninguna de las dos, retorna None
    if not resultados and not resultados2:
        return None

    # Inicializar variables
    nombre_apellidos = "Comprador" # Nombre por defecto
    if resultados:
        # Extraer el nombre de la primera coincidencia de la primera BD
        nombre_apellidos = resultados[0][0]

    # --- Procesar cartones de la Partida 1 ---
    cartones_vendidos1 = []
    for _, cartones_str in resultados:
        try:
            # Es más seguro usar ast.literal_eval que eval()
            cartones = ast.literal_eval(cartones_str)
            if isinstance(cartones, list):
                cartones_vendidos1.extend(int(carton) for carton in cartones)
        except (ValueError, SyntaxError):
            # Ignorar si hay un error en el formato de los cartones
            print(f"Advertencia: Error procesando cartones para la partida 1: {cartones_str}")

    # --- Procesar cartones de la Partida 2 ---
    cartones_vendidos2 = []
    for cartones_str, in resultados2: # El ", " desempaca la tupla de un solo elemento
        try:
            cartones = ast.literal_eval(cartones_str)
            if isinstance(cartones, list):
                cartones_vendidos2.extend(int(carton) for carton in cartones)
        except (ValueError, SyntaxError):
            print(f"Advertencia: Error procesando cartones para la partida 2: {cartones_str}")

    # Retornar los datos estructurados
    return {
        "nombre": nombre_apellidos,
        "cartones": cartones_vendidos1,  # Cartones de la partida 1
        "cartones2": cartones_vendidos2, # Cartones de la partida 2
        "venta1": partida1_titulo,       # Título para la partida 1
        "venta2": partida2_titulo        # Título para la partida 2
    }

def obtener_datos_partida():
    # Conectar a la base de datos
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    # Crear la consulta para obtener el dato específico (incluyendo imagen y total_cartones)
    cursor.execute("SELECT estatus, partida, recompensa, precio_de_carton, precio_dolar, zelle, modalidad_carton_regalo, imagen, total_cartones FROM partida WHERE id = 1")
    resultado = cursor.fetchone()
    conn.commit()

    if resultado and resultado[0] == "Venta finalizada":
        limite = resultado[8] if resultado[8] else 200
        cursor.execute("""DELETE FROM cartones_disponibles WHERE 1 = 1""")
        conn.commit()

        cursor.executemany("""
        INSERT OR IGNORE INTO cartones_disponibles (carton_disponible) VALUES (?);
        """, [(i,) for i in range(1, limite + 1)])
        conn.commit()



    conn.close()

    return resultado if resultado else None




def actualizar_partida(fecha_enunciado=None, recompensa=None, precio_carton=None, tipo_carton=None, action=None, precio_dolares=None, zelle=None, imagen=None, total_cartones=None):
    import sqlite3

    # Conectar a la base de datos
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    # Verificar si la tabla tiene al menos una fila
    cursor.execute("SELECT COUNT(*) FROM partida;")
    count = cursor.fetchone()[0]

    if count == 0:
        # Insertar una fila inicial con valores por defecto si no hay registros
        cursor.execute("""
            INSERT INTO partida (partida, recompensa, precio_de_carton, modalidad_carton_regalo, estatus, imagen, total_cartones)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, ("", "", 0.0, "", "Venta finalizada", "logo.png", 200))
        conn.commit()

    # Construcción dinámica de los campos y valores para el comando UPDATE
    fields = []
    values = []

    if fecha_enunciado:
        fields.append("partida = ?")
        values.append(fecha_enunciado)

    if recompensa:
        fields.append("recompensa = ?")
        values.append(recompensa)

    if precio_carton is not None:  # precio_carton puede ser 0, por eso se usa `is not None`
        fields.append("precio_de_carton = ?")
        values.append(precio_carton)

    if precio_dolares is not None:  # precio_dolares puede ser 0, por eso se usa `is not None`
        fields.append("precio_dolar = ?")
        values.append(precio_dolares)

    if zelle:  # precio_carton puede ser 0, por eso se usa `is not None`
        fields.append("zelle = ?")
        values.append(zelle)

    if tipo_carton:
        fields.append("modalidad_carton_regalo = ?")
        values.append(tipo_carton)

    if action:
        fields.append("estatus = ?")
        values.append(action)

    if imagen:
        fields.append("imagen = ?")
        values.append(imagen)

    if total_cartones is not None:
        fields.append("total_cartones = ?")
        values.append(total_cartones)

    # Actualizar la fila solo si hay campos a modificar
    if fields:
        update_query = f"UPDATE partida SET {', '.join(fields)} WHERE id = 1;"
        cursor.execute(update_query, values)

    # Confirmar los cambios y cerrar conexión
    conn.commit()
    conn.close()




def partida(C=None, read=None, U=None, D=None):
    if C:
        query = """
        INSERT OR REPLACE INTO partida (id, partida, hora_de_partida, precio_de_carton, estatus, mensaje)
        VALUES (1, ?, ?, ?, ?, ?);
        """
        execute_query(query, C)
    elif read:
        query = "SELECT * FROM partida WHERE id = 1;"
        return execute_query(query, fetch=True)
    elif U:
        query = """
        UPDATE partida
        SET partida = ?, hora_de_partida = ?, precio_de_carton = ?, estatus = ?, mensaje = ?
        WHERE id = 1;
        """
        execute_query(query, U)
    elif D:
        query = "DELETE FROM partida WHERE id = 1;"
        execute_query(query)

def cartones_disponibles(C=None, read=None, U=None, D=None):
    if C:
        query = "SELECT carton FROM cartones_usados;"
        return execute_query(query, fetch=True)
    elif read:
        if read == "*":  # Si `read` es "*", obten todos los registros
            query = "SELECT carton_disponible FROM cartones_disponibles;"
            return execute_query(query, fetch=True)
        else:
            query = "SELECT * FROM cartones_disponibles WHERE carton_disponible = ?;"
            return execute_query(query, (read,), fetch=True)



def cartones_usados(C=None, read=None, U=None, D=None):
    if C:
        query = "INSERT INTO cartones_usados (carton, usuario) VALUES (?, ?);"
        execute_query(query, C)
    elif read:
        query = "SELECT * FROM cartones_usados WHERE carton = ?;"
        return execute_query(query, (read,), fetch=True)
    elif U:
        query = """
        UPDATE cartones_usados
        SET usuario = ?
        WHERE carton = ?;
        """
        execute_query(query, U)
    elif D:
        query = "DELETE FROM cartones_usados WHERE carton = ?;"
        execute_query(query, (D,))

def requeridos(C=None, read=None, U=None, D=None, table="requeridos"):
    if C:
        query = f"""
        INSERT INTO {table}
        (nombre_apellidos, cedula, telefono, referencia, cartones_solicitados, monto, fecha)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        execute_query(query, C)
    elif read:
        query = f"SELECT * FROM {table} WHERE cedula = ?;"
        return execute_query(query, (read,), fetch=True)
    elif U:
        query = f"""
        UPDATE {table}
        SET nombre_apellidos = ?, telefono = ?, referencia = ?,
            cartones_solicitados = ?, monto = ?, fecha = ?
        WHERE cedula = ?;
        """
        execute_query(query, U)
    elif D:
        query = f"DELETE FROM {table} WHERE cedula = ?;"
        execute_query(query, (D,))

def usuarios_aceptados(C=None, read=None, U=None, D=None):
    requeridos(C, read, U, D, table="usuarios_aceptados")

# Función para la tabla "cartones_usados"
def cartones_usados(C=None, read=None, U=None, D=None):
    if C:  # Insertar un nuevo cartón
        query = "INSERT OR IGNORE INTO cartones_usados (carton, usuario) VALUES (?, ?);"
        execute_query(query, C)
    elif read:  # Leer registros
        if read == "*":  # Leer todos los registros
            query = "SELECT carton FROM cartones_usados;"
            return execute_query(query, fetch=True)
        else:  # Leer un registro específico
            query = "SELECT * FROM cartones_usados WHERE carton = ?;"
            return execute_query(query, (read,), fetch=True)
    elif U:  # Actualizar un registro
        query = """
        UPDATE cartones_usados
        SET usuario = ?
        WHERE carton = ?;
        """
        execute_query(query, U)
    elif D:  # Eliminar un registro
        query = "DELETE FROM cartones_usados WHERE carton = ?;"
        execute_query(query, (D,))




def get_data():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    # Consulta todos los datos de la tabla
    cursor.execute("""
            SELECT *
            FROM requeridos
            WHERE id IN (
                SELECT MIN(id)
                FROM requeridos
                GROUP BY cartones_solicitados
            );
        """)
    rows = cursor.fetchall()
    conn.close()

    # Convertir los resultados en una lista de diccionarios
    solicitudes = []
    for row in rows:
        solicitud = {
            "id": row[0],
            "nombre": row[1],
            "cedula": row[2],
            "telefono": row[3],
            "referencia": row[4],
            "cartones": row[5],
            "monto": row[6],
            "fecha": row[7],
            "estatus": row[8],
            "link": row[9]
        }
        solicitudes.append(solicitud)

    return solicitudes


def get_datatop():
    import sqlite3

    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    # Consulta para agrupar por cedula y sumar el campo length
    cursor.execute("""
        SELECT
            MIN(id) AS id,
            nombre_apellidos,
            cedula,
            telefono,
            referencia,
            GROUP_CONCAT(cartones_solicitados) AS cartones, -- Concatenamos los cartones solicitados
            SUM(monto) AS monto,                         -- Sumamos el monto
            fecha,
            estatus,
            link,
            SUM(
                (SELECT LENGTH(REPLACE(REPLACE(cartones_solicitados, '[', ''), ']', '')) - LENGTH(REPLACE(REPLACE(cartones_solicitados, ',', ''), '[', '')) + 2)
        FROM requeridos
        WHERE estatus = 'aprobado'
        GROUP BY cedula                                 -- Agrupamos por cedula
    """)

    rows = cursor.fetchall()
    conn.close()

    # Convertir los resultados en una lista de diccionarios
    solicitudes = []
    for row in rows:
        solicitud = {
            "id": row[0],
            "nombre": row[1],
            "cedula": row[2],
            "telefono": row[3],
            "referencia": row[4],
            "cartones": row[5],   # Concatenados en caso de que sean varios
            "monto": row[6],      # Suma de todos los montos
            "fecha": row[7],
            "estatus": row[8],
            "link": row[9],
            "length": row[10],    # Suma del campo length
        }
        solicitudes.append(solicitud)

    return solicitudes



def get_enunciado():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    cursor.execute("SELECT estatus FROM partida WHERE id = 1")
    estatus = cursor.fetchone()[0]
    conn.commit()

    if estatus == "Venta en curso":

        cursor.execute("SELECT partida FROM partida")
        data = cursor.fetchone()  # Recupera todos los datos de la tabla
        conn.close()

    else:

        data = ["No hay cartones disponibles"]

    return data[0] if data else None

def get_premio():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT recompensa FROM partida")
    data = cursor.fetchone()  # Recupera todos los datos de la tabla
    conn.close()
    return data[0] if data else None

def get_precio():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT precio_de_carton FROM partida")
    data = cursor.fetchone()  # Recupera todos los datos de la tabla
    conn.close()
    return data[0] if data else None


from flask import Flask, redirect, url_for

def insertar_comprador(nombre_apellido, cedula, telefono, referencia, cartones_solicitados, monto, fecha, referencia_ruta, link, cartones_solicitados_str, max_retries=3, delay=2):
    cartones_solicitados = [int(carton.strip()) for carton in cartones_solicitados_str.split(",")]
    cartones_solicitados_text = json.dumps(cartones_solicitados)  # JSON format (recommended)

    # Intentar varias veces si falla
    attempt = 0
    while attempt < max_retries:
        try:
            # Conectar a la base de datos
            conn = sqlite3.connect('bingo.db')
            cursor = conn.cursor()

            # Iniciar la transacción explícitamente
            conn.execute("BEGIN TRANSACTION;")

            # Consultar si los cartones solicitados existen en la tabla 'cartones_disponibles'
            placeholders = ', '.join(['?'] * len(cartones_solicitados))
            query = f"SELECT carton_disponible FROM cartones_disponibles WHERE carton_disponible IN ({placeholders})"
            cursor.execute(query, cartones_solicitados)
            cartones_disponibles = [row[0] for row in cursor.fetchall()]
            cursor.execute(f"DELETE FROM cartones_disponibles WHERE carton_disponible IN ({placeholders});", cartones_solicitados)
            conn.commit()

            # Si la cantidad de cartones encontrados no coincide con la cantidad solicitada, significa que algunos cartones no están disponibles
            if len(cartones_disponibles) != len(cartones_solicitados):
                # Si no todos los cartones están disponibles, esperar y reintentar
                attempt += 1
                conn.execute("ROLLBACK;")
                conn.close()
                if attempt < max_retries:
                    print(f"Intento {attempt} fallido, reintentando...")
                    time.sleep(delay)  # Esperar un poco antes de reintentar
                    continue  # Volver a intentar la consulta
                else:
                    # Si se superan los intentos, retornar un mensaje
                    print("insercion invalida")
                    conn = sqlite3.connect('bingo.db')
                    cursor = conn.cursor()




            # Ejecutar el comando para eliminar los cartones de la tabla `cartones_disponibles`
            cursor.execute(f"DELETE FROM cartones_disponibles WHERE carton_disponible IN ({placeholders});", cartones_solicitados)
            conn.commit()

            # Si todos los cartones están disponibles, proceder con la inserción en la tabla 'requeridos'
            cursor.execute("""
                INSERT INTO requeridos (
                    nombre_apellidos,
                    cedula,
                    telefono,
                    referencia,
                    cartones_solicitados,
                    monto,
                    fecha,
                    link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (nombre_apellido, cedula, telefono, referencia_ruta, cartones_solicitados_text, monto, fecha, link))

            print('insercion exitosa')


            # Confirmar la inserción y eliminación
            conn.execute("COMMIT;")

            # Cerrar la conexión
            conn.close()
            break  # Si la operación fue exitosa, salir del bucle

        except sqlite3.OperationalError as e:
            # Si hay un error de base de datos, hacer rollback y esperar antes de reintentar
            conn.execute("ROLLBACK;")
            conn.close()
            print(f"Error al insertar comprador, reintentando: {e}")
            attempt += 1
            time.sleep(delay)  # Esperar un poco antes de reintentar

    # Si se superan los intentos, retornar un error o un mensaje
    print("No se pudo procesar la compra después de varios intentos, por favor intente más tarde.")




def get_estatus():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT estatus FROM partida WHERE id = 1")
    estatus = cursor.fetchone()[0]
    conn.close()
    return estatus if estatus else None

def get_modalidad():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT modalidad_carton_regalo FROM partida WHERE id = 1")
    modalidad = cursor.fetchone()[0]
    conn.close()
    return modalidad if modalidad else None

def vendidos(cartones):
    # Conectar a la base de datos
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    # Convertir los valores del array en tuplas (executemany espera una lista de tuplas)
    cartones_tuplas = [(carton,) for carton in cartones]

    try:
        # Ejecutar el comando para insertar múltiples valores
        cursor.executemany("""
            INSERT INTO cartones_usados (carton) VALUES (?);
        """, cartones_tuplas)

        # Confirmar cambios
        conn.commit()
        print(f"Cartones insertados: {cartones}")
    except sqlite3.IntegrityError as e:
        print(f"Error al insertar cartones: {e}")
    finally:
        # Cerrar la conexión
        conn.close()

def get_dolar():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT precio_dolar FROM partida WHERE id = 1")
    dolar = cursor.fetchone()[0]
    conn.close()
    return dolar if dolar else None

def get_zelle():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT zelle FROM partida WHERE id = 1")
    zelle = cursor.fetchone()[0]
    conn.close()
    return zelle if zelle else None



def reintegrar_cartones(cartones):
    # Conectar a la base de datos
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    # Convertir los valores del array en tuplas (executemany espera una lista de tuplas)
    cartones_tuplas = [(carton,) for carton in cartones]

    try:
        # Ejecutar el comando para insertar múltiples valores
        cursor.executemany("""
        INSERT OR IGNORE INTO cartones_disponibles (carton_disponible) VALUES (?);
        """, cartones_tuplas)


        # Confirmar cambios
        conn.commit()
        print(f"Cartones reintegrados: {cartones}")
    except sqlite3.IntegrityError as e:
        print(f"Error al reintegrar cartones: {e}")
    finally:
        # Cerrar la conexión
        conn.close()

def get_porcentaje(flag):
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(carton_disponible) FROM cartones_disponibles")
    cantidad = cursor.fetchone()[0]
    
    cursor.execute("SELECT total_cartones FROM partida WHERE id = 1")
    res_total = cursor.fetchone()
    total = res_total[0] if res_total and res_total[0] else 200
    conn.close()
    
    if flag == False:
        return cantidad

    # Calcular el porcentaje
    porcentaje = (cantidad / total) * 100
    return round(porcentaje, 2)

def get_imagen():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT imagen FROM partida WHERE id = 1")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res and res[0] else "logo.png"

def asignar_cartones_aleatorios(cantidad, session_id):
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    
    # 1. Limpiar cartones expirados
    cursor.execute("DELETE FROM cartones_temporales WHERE timestamp <= datetime('now', '-25 minutes')")
    conn.commit()
    
    # 2. Seleccionar N cartones aleatorios que estén disponibles y no reservados por otros
    cursor.execute("""
        SELECT carton_disponible FROM cartones_disponibles
        WHERE carton_disponible NOT IN (
            SELECT carton FROM cartones_temporales WHERE session_id != ?
        )
        ORDER BY RANDOM()
        LIMIT ?
    """, (session_id, cantidad))
    
    cartones = [str(row[0]) for row in cursor.fetchall()]
    
    # 3. Reservar para esta sesión si encontramos cartones
    if cartones:
        cursor.execute("DELETE FROM cartones_temporales WHERE session_id = ?", (session_id,))
        cartones_para_insertar = [(c, session_id) for c in cartones]
        cursor.executemany("INSERT INTO cartones_temporales (carton, session_id) VALUES (?, ?)", cartones_para_insertar)
        conn.commit()
        
    conn.close()
    return cartones

def get_limite_cartones():
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()
    cursor.execute("SELECT total_cartones FROM partida WHERE id = 1")
    res = cursor.fetchone()
    conn.close()
    return res[0] if res and res[0] else 200