from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from crud import get_datatop, obtener_comprador_por_cedula, get_porcentaje, cartones_disponibles,cartones_usados,reintegrar_cartones,get_data,actualizar_partida,obtener_datos_partida, get_enunciado, get_premio, insertar_comprador, get_estatus, get_precio, vendidos, get_modalidad, get_dolar, get_zelle
from crud2 import get_datatop2, get_porcentaje2, cartones_disponibles2,cartones_usados2,reintegrar_cartones2,get_data2,actualizar_partida2,obtener_datos_partida2, get_enunciado2, get_premio2, insertar_comprador2, get_estatus2, get_precio2, vendidos2, get_modalidad2, get_dolar2, get_zelle2
import os
from werkzeug.utils import secure_filename
from functools import wraps
import sqlite3
from datetime import datetime
import random
import string
import re
import time
import uuid # Para generar identificadores únicos de sesión




# Decorador para proteger las rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):  # Verifica si el usuario está autenticado
            return redirect(url_for('admin_index'))  # Redirige al login si no está autenticado
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
UPLOAD_FOLDER = 'static/comprobantes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'supersecretkey'
socketio = SocketIO(app, manage_session=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def init_db():
    with sqlite3.connect("bingo.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cartones_temporales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carton TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def init_db2():
    with sqlite3.connect("bingo2.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cartones_temporales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                carton TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()
init_db2()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=["GET"])
def index():
    return render_template('index.html', enunciado=get_enunciado(), enunciado2=get_enunciado2())



def generar_sufijo_aleatorio(length=6):
    # Genera un sufijo aleatorio de letras y números
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choices(caracteres, k=length))

@app.route("/cartones", methods=["GET"])
def imprimir_cartones():
    estatus = get_estatus()
    if estatus == "Venta finalizada":
        return redirect(url_for('index'))  # redirigir a un panel de administración

    cartones_tuplas = cartones_disponibles(read="*")
    cartones = [carton[0] for carton in cartones_tuplas]

    return render_template("seleccion_cartones.html", cartones=cartones,
                           precio=int(get_precio()), modalidad=get_modalidad(),
                           precio_dolares=get_dolar(), venta='uno', porcentaje = get_porcentaje(True), solicitudes = get_datatop())


@app.route("/compra", methods=["POST", "GET"])
def pago():
    if request.method == "POST":
        # --- 1. Gestión de la Sesión del Usuario ---
        # Si el usuario no tiene una sesión, le creamos una.
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        user_session_id = session['session_id']

        cartones_seleccionados = request.form.getlist("cartones")
        if len(cartones_seleccionados) == 1 and ',' in cartones_seleccionados[0]:
            cartones_seleccionados = cartones_seleccionados[0].split(',')

        with sqlite3.connect("bingo.db") as conn:
            cursor = conn.cursor()
            # Limpiamos los cartones expirados de CUALQUIER sesión
            cursor.execute("DELETE FROM cartones_temporales WHERE timestamp <= datetime('now', '-25 minutes')")
            conn.commit()

            # --- 2. Verificación de Duplicados (Modificada) ---
            # Ahora buscamos cartones que estén en la DB pero que NO pertenezcan a la sesión del usuario actual.
            placeholders = ', '.join('?' for _ in cartones_seleccionados)
            sql_query = f"SELECT carton FROM cartones_temporales WHERE carton IN ({placeholders}) AND session_id != ?"

            # Los parámetros ahora incluyen el ID de la sesión del usuario al final
            params = cartones_seleccionados + [user_session_id]
            cursor.execute(sql_query, params)
            duplicados = cursor.fetchall()

            if duplicados:
                # La lógica para mostrar el error si hay duplicados no cambia.
                duplicados_list = [carton[0] for carton in duplicados]
                if len(duplicados_list) == 1:
                    flash(f"El cartón {duplicados_list[0]} ya ha sido seleccionado por otro usuario.", "warning")
                else:
                    flash(f"Los cartones {', '.join(duplicados_list)} ya han sido seleccionados por otro usuario.", "warning")
                return redirect(url_for("imprimir_cartones"))

            # --- 3. Inserción en la Base de Datos (Modificada) ---
            # Primero, borramos la selección ANTERIOR de este mismo usuario para evitar conflictos.
            cursor.execute("DELETE FROM cartones_temporales WHERE session_id = ?", (user_session_id,))

            # Insertamos los nuevos cartones asociándolos a la sesión del usuario.
            cartones_para_insertar = [(c, user_session_id) for c in cartones_seleccionados]
            cursor.executemany("INSERT INTO cartones_temporales (carton, session_id) VALUES (?, ?)", cartones_para_insertar)
            conn.commit()
        total_price = float(request.form["total"])  # Total en bolívares
        total_price_2 = float(request.form["total2"])  # Total en dólares

        # Pasar los valores al template
        return render_template(
            "comprar.html",
            cartones_seleccionados=', '.join(cartones_seleccionados),
            total_price=total_price,
            total_price2=total_price_2,
            premio=get_premio(),
            precio=int(get_precio()),
            enunciado=get_enunciado(),
            zelle=get_zelle(),
            precio_dolares=get_dolar(),
            venta='uno'
        )

    # Si no es POST, solo se muestran los datos vacíos
    return render_template("comprar.html", cartones_seleccionados='', total_price=0,
                           premio=get_premio(), precio=int(get_precio()), enunciado=get_enunciado(),
                           total_price2=0, zelle=get_zelle(), precio_dolares=get_dolar(), venta='uno')



@app.route("/registrar_compra", methods=["POST", "GET"])
def registrar():
    if request.method == "POST":


        # Recuperar los datos del formulario
        nombre = request.form["nombre"]
        cedula = request.form["cedula"]
        nmr_te = request.form["telefono"]
        nmr_r = request.files["referencia"]

        # Validar y guardar el archivo de referencia si es necesario
        if nmr_r and allowed_file(nmr_r.filename):
            filename = secure_filename(nmr_r.filename)
            # Agregar un sufijo aleatorio al nombre del archivo
            nombre_archivo, extension = os.path.splitext(filename)
            sufijo = generar_sufijo_aleatorio()
            filename = f"{nombre_archivo}_{sufijo}{extension}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            nmr_r.save(filepath)

            referencia_ruta = os.path.join('/static/comprobantes', filename).replace("\\", "/")
            fecha = get_enunciado()

        # Recuperar los datos de la compra (los valores pasados en los campos ocultos)
        cartones_seleccionados_str = request.form.get("cartones_seleccionados", "")
        total_price = request.form.get("total_price", 0)
        total_price_2 = request.form.get("total_price_2", 0)

        link = f"/{cedula}"

        # Insertar los datos en la base de datos
        insertar_comprador(
            nombre, cedula, nmr_te, nmr_r.filename, cartones_seleccionados_str,
            f"{total_price}bs/{total_price_2}$",
            fecha, referencia_ruta, link, cartones_seleccionados_str
        )

        return render_template('confirmacion.html')

@app.route('/descargar_cartones')
def descargar_cartones():
    cartones = request.args.get('cartones', '')
    cartones_lista = cartones.split(',')

    # Puedes devolver una vista donde se muestran las imágenes de los cartones
    return render_template('descargar_cartones.html', cartones=cartones_lista)


@app.route("/cartones2", methods=["GET"])
def imprimir_cartones2():
    estatus = get_estatus2()
    if estatus == "Venta finalizada":
        return redirect(url_for('index'))  # redirigir a un panel de administración

    cartones_tuplas = cartones_disponibles2(read="*")
    cartones = [carton[0] for carton in cartones_tuplas]

    return render_template("seleccion_cartones.html", cartones=cartones,
                           precio=int(get_precio2()), modalidad=get_modalidad2(),
                           precio_dolares=get_dolar2(), venta='dos', porcentaje=get_porcentaje2(True), solicitudes = get_datatop2())


@app.route("/compra2", methods=["POST", "GET"])
def pago2():
    if request.method == "POST":
        # --- 1. Gestión de la Sesión del Usuario ---
        # Si el usuario no tiene una sesión, le creamos una.
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        user_session_id = session['session_id']

        cartones_seleccionados = request.form.getlist("cartones")
        if len(cartones_seleccionados) == 1 and ',' in cartones_seleccionados[0]:
            cartones_seleccionados = cartones_seleccionados[0].split(',')

        with sqlite3.connect("bingo2.db") as conn:
            cursor = conn.cursor()
            # Limpiamos los cartones expirados de CUALQUIER sesión
            cursor.execute("DELETE FROM cartones_temporales WHERE timestamp <= datetime('now', '-25 minutes')")
            conn.commit()

            # --- 2. Verificación de Duplicados (Modificada) ---
            # Ahora buscamos cartones que estén en la DB pero que NO pertenezcan a la sesión del usuario actual.
            placeholders = ', '.join('?' for _ in cartones_seleccionados)
            sql_query = f"SELECT carton FROM cartones_temporales WHERE carton IN ({placeholders}) AND session_id != ?"

            # Los parámetros ahora incluyen el ID de la sesión del usuario al final
            params = cartones_seleccionados + [user_session_id]
            cursor.execute(sql_query, params)
            duplicados = cursor.fetchall()

            if duplicados:
                # La lógica para mostrar el error si hay duplicados no cambia.
                duplicados_list = [carton[0] for carton in duplicados]
                if len(duplicados_list) == 1:
                    flash(f"El cartón {duplicados_list[0]} ya ha sido seleccionado por otro usuario.", "warning")
                else:
                    flash(f"Los cartones {', '.join(duplicados_list)} ya han sido seleccionados por otro usuario.", "warning")
                return redirect(url_for("imprimir_cartones2"))

            # --- 3. Inserción en la Base de Datos (Modificada) ---
            # Primero, borramos la selección ANTERIOR de este mismo usuario para evitar conflictos.
            cursor.execute("DELETE FROM cartones_temporales WHERE session_id = ?", (user_session_id,))

            # Insertamos los nuevos cartones asociándolos a la sesión del usuario.
            cartones_para_insertar = [(c, user_session_id) for c in cartones_seleccionados]
            cursor.executemany("INSERT INTO cartones_temporales (carton, session_id) VALUES (?, ?)", cartones_para_insertar)
            conn.commit()

        total_price = float(request.form["total"])   # Total en bolívares
        total_price_2 = float(request.form["total2"])  # Total en dólares

        return render_template(
            "comprar.html",
            cartones_seleccionados=', '.join(cartones_seleccionados),
            total_price=total_price,
            total_price2=total_price_2,
            premio=get_premio2(),
            precio=int(get_precio2()),
            enunciado=get_enunciado2(),
            zelle=get_zelle2(),
            precio_dolares=get_dolar2(),
            venta='dos'
        )

    # Si no es POST, se muestran los datos vacíos
    return render_template("comprar.html", cartones_seleccionados='', total_price=0,
                           premio=get_premio2(), precio=int(get_precio2()), enunciado=get_enunciado2(),
                           total_price2=0, zelle=get_zelle2(), precio_dolares=get_dolar2(), venta='dos')


@app.route("/registrar_compra2", methods=["POST", "GET"])
def registrar2():
    if request.method == "POST":
        # Recuperar los datos del formulario
        nombre = request.form["nombre"]
        cedula = request.form["cedula"]
        nmr_te = request.form["telefono"]
        nmr_r = request.files["referencia"]

        # Validar y guardar el archivo de referencia si es necesario
        if nmr_r and allowed_file(nmr_r.filename):
            filename = secure_filename(nmr_r.filename)
            nombre_archivo, extension = os.path.splitext(filename)
            sufijo = generar_sufijo_aleatorio()
            filename = f"{nombre_archivo}_{sufijo}{extension}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            nmr_r.save(filepath)

            referencia_ruta = os.path.join('/static/comprobantes', filename).replace("\\", "/")
            fecha = get_enunciado2()

        # Recuperar los datos de la compra (los valores pasados en los campos ocultos)
        cartones_seleccionados_str = request.form.get("cartones_seleccionados", "")
        total_price = request.form.get("total_price", 0)
        total_price_2 = request.form.get("total_price_2", 0)

        link = f"/descargar_cartones2?cartones={cartones_seleccionados_str}"

        # Insertar los datos en la base de datos
        insertar_comprador2(
            nombre, cedula, nmr_te, nmr_r.filename, cartones_seleccionados_str,
            f"{total_price}bs/{total_price_2}$",
            fecha, referencia_ruta, link, cartones_seleccionados_str
        )

        return render_template('confirmacion.html')






@app.route('/descargar_cartones2')
def descargar_cartones2():
    cartones = request.args.get('cartones', '')
    cartones_lista = cartones.split(',')

    # Retornar una vista donde se muestran las imágenes de los cartones
    return render_template('descargar_cartones.html', cartones=cartones_lista)


@app.route("/admin", methods=["GET", "POST"])
def admin_index():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin456**":
            session['logged_in'] = True  # Establece que el usuario está autenticado
            return redirect(url_for('admin_dashboard'))  # redirigir a un panel de administración
        else:
            error_message = "Usuario o contraseña incorrectos"
            return render_template("login.html", error_message=error_message)

    return render_template("login.html")

"""elimine las rutas puente de carton y usuario y usuario requerido a usuario verificado porque NO SE PORQUE NO OBTENGO EL CARTON SI LO ESTA ENVIADNO AL SERVIDOR"""
@app.route("/admin/dashboard")
@login_required  # Ruta protegida por login

def admin_dashboard():
    return render_template("panel_admin.html")

@app.route("/admin/dashboard/partida" , methods = ["POST" , "GET"])
@login_required  # Ruta protegida por login

def admin_dashboard_partida():
    datos = obtener_datos_partida()

    if request.method == "POST":
        action = request.form.get("action")  # "reiniciar" o "detener"
        fecha_enunciado = request.form.get("fechaEnunciado")
        recompensa = request.form.get("recompensa")
        precio_carton = request.form.get("precioCarton")
        tipo_carton = request.form.get("tipoCarton")
        precio_dolares = request.form.get("precioCarton$")
        zelle = request.form.get("zelle")
        actualizar_partida(fecha_enunciado, recompensa, precio_carton, tipo_carton, action, precio_dolares, zelle)
        return redirect(url_for('admin_dashboard_partida'))  # redirigir a un panel de administración
    return render_template("admin_partida.html", datos=datos, venta='uno')



@app.route("/admin/dashboard/partida/reiniciar" , methods = ["POST"])
@login_required  # Ruta protegida por login
def reiniciar():

    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    cursor.execute("""DELETE FROM cartones_disponibles WHERE 1 = 1""")
    conn.commit()

    cursor.execute("""DELETE FROM requeridos WHERE 1 = 1""")
    conn.commit()

    cursor.executemany("""
    INSERT OR IGNORE INTO cartones_disponibles (carton_disponible) VALUES (?);
    """, [(i,) for i in range(1, 201)])
    conn.commit()

    conn.close()

        # Eliminar todos los archivos en /static/comprobantes/
    folder_path = 'static/comprobantes/'
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):  # Verificar si es un archivo
            os.remove(file_path)

    # Redirigir al panel de administración
    return redirect(url_for('admin_dashboard_partida'))

@app.route("/verify", methods=["POST", "GET"])
def verificar():
    return render_template("verificar.html")


@app.route('/<cedula>')
def view_data(cedula):
    """
    Renderiza una plantilla HTML con el nombre y los cartones asociados a la cédula.
    """
    # Obtener datos del comprador desde la base de datos (implementar lógica en tu función)
    comprador = obtener_comprador_por_cedula(cedula)  # Ejemplo de función
    if not comprador:
        return redirect(url_for('verificar'))
    cartones2 = comprador["cartones2"]
    nombre = comprador["nombre"]
    cartones = comprador["cartones"]
    venta1 = comprador["venta1"]
    venta2 = comprador["venta2"]

    # Renderizar la plantilla con los datos
    return render_template('descargar_cartones.html', nombre=nombre, cartones=cartones, cartones2=cartones2, venta1=venta1, venta2=venta2)


@app.route("/admin/dashboard/solicitudes")
@login_required  # Ruta protegida por login
def admin_dashboard_solicitudes():
    solicitudes = get_data()  # Recupera los datos de la tabla
    return render_template("admin_solicitudes.html", solicitudes=solicitudes)


@app.route("/admin/dashboard/solicitudes/top")
@login_required  # Ruta protegida por login
def top():
    solicitudes = get_datatop()
    return render_template("top.html", solicitudes = solicitudes)


@app.route("/admin/dashboard/solicitudes/invalidate/", methods=["POST"])
def invalidate():
    data = request.get_json()
    solicitud_id = data.get("id")

    # Conectar a la base de datos
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    try:
        # Obtener los cartones asociados a la solicitud
        cursor.execute("""SELECT cartones_solicitados FROM requeridos WHERE id = ?""", (solicitud_id,))
        cartones_solicitados = cursor.fetchone()

        if not cartones_solicitados:
            return jsonify({"success": False, "message": "Solicitud no encontrada"}), 404

        # Extraer los cartones vendidos como texto
        cartones_texto = cartones_solicitados[0]  # Obtener el primer resultado
        if isinstance(cartones_texto, str):
            cartones = [int(carton.strip()) for carton in cartones_texto.strip('[]').split(',') if carton.strip().isdigit()]
        else:
            cartones = [int(cartones_texto)]


        # Reintegrar los cartones a la tabla de disponibles
        reintegrar_cartones(cartones)

        # Actualizar el estado de la solicitud como invalidada
        cursor.execute("""UPDATE requeridos SET estatus = "invalidado" WHERE id = ?""", (solicitud_id,))
        conn.commit()
        cursor.execute("""DELETE FROM requeridos WHERE id = ?""", (solicitud_id,))
        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        conn.close()

    return redirect(url_for('admin_dashboard_solicitudes'))  # redirigir a un panel de administración




"""ELIMINE ESTA SECCION AUNQUE CON EL MISMO PROTOCOLO MUESTRO TODO Y YA , SOLO ESE PROBLEMA DE CARTONES """

@app.route("/admin/dashboard/solicitudes/message/", methods=["POST"])
def message():
    data = request.get_json()
    solicitud_id = data.get("id")

    # Conectar a la base de datos
    conn = sqlite3.connect('bingo.db')
    cursor = conn.cursor()

    # Verificar si la solicitud existe
    cursor.execute("""UPDATE requeridos SET estatus = "enviado" WHERE id = ?""", (solicitud_id,))
    conn.commit()

    # Extraer los cartones vendidos como texto
    cursor.execute("""SELECT cartones_solicitados FROM requeridos WHERE id = ?""", (solicitud_id,))
    cartones_vendidos = cursor.fetchone()[0]  # Obtener el primer resultado
    conn.close()

    # Limpieza y conversión del string a lista de enteros
    if isinstance(cartones_vendidos, str):
        # Eliminar caracteres no deseados y dividir el string
        cartones = [int(carton.strip()) for carton in cartones_vendidos.strip('[]').split(',') if carton.strip().isdigit()]
    else:
        # Si no es un string, manejarlo como un único valor
        cartones = [int(cartones_vendidos)]


    # Llamar a la función para insertar los cartones
    vendidos(cartones)

    return redirect(url_for('admin_dashboard_solicitudes'))  # redirigir a un panel de administración



@app.route("/admin/dashboard/vendidos")
@login_required  # Ruta protegida por login
def mostrar_cartones():
    with sqlite3.connect("bingo.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cartones_solicitados FROM requeridos;")
        cartones_tuplas = cursor.fetchall()
        conn.commit()
        cursor.execute("""
            SELECT monto
            FROM requeridos
            WHERE id IN (
                SELECT MIN(id)
                FROM requeridos
                GROUP BY cartones_solicitados
            );
        """)
        montos = cursor.fetchall()

        # Procesar los montos
        total_bs = 0
        total_dolar = 0

        for monto in montos:
            if monto and monto[0]:
                # Expresión regular para separar los montos antes de 'bs' y entre '/' y '$'
                match_bs = re.search(r'([\d.]+)bs', monto[0])
                match_dolar = re.search(r'/([\d.]+)\$', monto[0])

                if match_bs:
                    total_bs += float(match_bs.group(1))
                if match_dolar:
                    total_dolar += float(match_dolar.group(1))

        montos_totales = f"{total_bs}bs/{total_dolar}$"

        # Usar un conjunto para evitar duplicados
        cartones_set = set()
        for carton in cartones_tuplas:
            if carton[0]:  # Evitar errores con valores vacíos o nulos
                numeros = eval(carton[0]) if isinstance(carton[0], str) else carton[0]
                if isinstance(numeros, list):
                    cartones_set.update(numeros)
                else:
                    cartones_set.add(numeros)

        # Convertir el conjunto a lista para pasar a la plantilla
        cartones = list(cartones_set)

        return render_template("disponibles_no.html", cartones=cartones, montos_totales=montos_totales)

@app.route("/admin/dashboard/partida2" , methods = ["POST" , "GET"])
@login_required  # Ruta protegida por login

def admin_dashboard_partida2():
    datos = obtener_datos_partida2()

    if request.method == "POST":
        action = request.form.get("action")  # "reiniciar" o "detener"
        fecha_enunciado = request.form.get("fechaEnunciado")
        recompensa = request.form.get("recompensa")
        precio_carton = request.form.get("precioCarton")
        tipo_carton = request.form.get("tipoCarton")
        precio_dolares = request.form.get("precioCarton$")
        zelle = request.form.get("zelle")
        actualizar_partida2(fecha_enunciado, recompensa, precio_carton, tipo_carton, action, precio_dolares, zelle)
        return redirect(url_for('admin_dashboard_partida2'))  # redirigir a un panel de administración
    return render_template("admin_partida.html", datos=datos, venta='dos')


@app.route("/admin/dashboard/partida2/reiniciar" , methods = ["POST"])
@login_required  # Ruta protegida por login
def reiniciar2():

    conn = sqlite3.connect('bingo2.db')
    cursor = conn.cursor()

    cursor.execute("""DELETE FROM cartones_disponibles WHERE 1 = 1""")
    conn.commit()

    cursor.execute("""DELETE FROM requeridos WHERE 1 = 1""")
    conn.commit()

    cursor.executemany("""
    INSERT OR IGNORE INTO cartones_disponibles (carton_disponible) VALUES (?);
    """, [(i,) for i in range(1, 201)])
    conn.commit()

    conn.close()

        # Eliminar todos los archivos en /static/comprobantes/
    folder_path = 'static/comprobantes/'
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):  # Verificar si es un archivo
            os.remove(file_path)

    # Redirigir al panel de administración
    return redirect(url_for('admin_dashboard_partida2'))

@app.route("/admin/dashboard/solicitudes2")
@login_required  # Ruta protegida por login
def admin_dashboard_solicitudes2():
    solicitudes = get_data2()  # Recupera los datos de la tabla
    return render_template("admin_solicitudes.html", solicitudes=solicitudes)

@app.route("/admin/dashboard/solicitudes/top")
@login_required  # Ruta protegida por login
def top2():
    solicitudes = get_datatop2()
    return render_template("top.html", solicitudes = solicitudes)

@app.route("/admin/dashboard/solicitudes2/invalidate/", methods=["POST"])
def invalidate2():
    data = request.get_json()
    solicitud_id = data.get("id")

    # Conectar a la base de datos
    conn = sqlite3.connect('bingo2.db')
    cursor = conn.cursor()

    try:
        # Obtener los cartones asociados a la solicitud
        cursor.execute("""SELECT cartones_solicitados FROM requeridos WHERE id = ?""", (solicitud_id,))
        cartones_solicitados = cursor.fetchone()

        if not cartones_solicitados:
            return jsonify({"success": False, "message": "Solicitud no encontrada"}), 404

        # Extraer los cartones vendidos como texto
        cartones_texto = cartones_solicitados[0]  # Obtener el primer resultado
        if isinstance(cartones_texto, str):
            cartones = [int(carton.strip()) for carton in cartones_texto.strip('[]').split(',') if carton.strip().isdigit()]
        else:
            cartones = [int(cartones_texto)]


        # Reintegrar los cartones a la tabla de disponibles
        reintegrar_cartones2(cartones)

        # Actualizar el estado de la solicitud como invalidada
        cursor.execute("""UPDATE requeridos SET estatus = "invalidado" WHERE id = ?""", (solicitud_id,))
        conn.commit()
        cursor.execute("""DELETE FROM requeridos WHERE id = ?""", (solicitud_id,))
        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        conn.close()

    return redirect(url_for('admin_dashboard_solicitudes2'))  # redirigir a un panel de administración


@app.route("/admin/dashboard/solicitudes2/message/", methods=["POST"])
def message2():
    data = request.get_json()
    solicitud_id = data.get("id")

    # Conectar a la base de datos
    conn = sqlite3.connect('bingo2.db')
    cursor = conn.cursor()

    # Verificar si la solicitud existe
    cursor.execute("""UPDATE requeridos SET estatus = "enviado" WHERE id = ?""", (solicitud_id,))
    conn.commit()

    # Extraer los cartones vendidos como texto
    cursor.execute("""SELECT cartones_solicitados FROM requeridos WHERE id = ?""", (solicitud_id,))
    cartones_vendidos = cursor.fetchone()[0]  # Obtener el primer resultado
    conn.close()

    # Limpieza y conversión del string a lista de enteros
    if isinstance(cartones_vendidos, str):
        # Eliminar caracteres no deseados y dividir el string
        cartones = [int(carton.strip()) for carton in cartones_vendidos.strip('[]').split(',') if carton.strip().isdigit()]
    else:
        # Si no es un string, manejarlo como un único valor
        cartones = [int(cartones_vendidos)]


    # Llamar a la función para insertar los cartones
    vendidos2(cartones)

    return redirect(url_for('admin_dashboard_solicitudes2'))  # redirigir a un panel de administración



@app.route("/admin/dashboard/vendidos2")
@login_required  # Ruta protegida por login
def mostrar_cartones2():
    with sqlite3.connect("bingo2.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cartones_solicitados FROM requeridos;")
        cartones_tuplas = cursor.fetchall()
        conn.commit()
        cursor.execute("""
            SELECT monto
            FROM requeridos
            WHERE id IN (
                SELECT MIN(id)
                FROM requeridos
                GROUP BY cartones_solicitados
            );
        """)
        montos = cursor.fetchall()

        # Procesar los montos
        total_bs = 0
        total_dolar = 0

        for monto in montos:
            if monto and monto[0]:
                # Expresión regular para separar los montos antes de 'bs' y entre '/' y '$'
                match_bs = re.search(r'([\d.]+)bs', monto[0])
                match_dolar = re.search(r'/([\d.]+)\$', monto[0])

                if match_bs:
                    total_bs += float(match_bs.group(1))
                if match_dolar:
                    total_dolar += float(match_dolar.group(1))

        montos_totales = f"{total_bs}bs/{total_dolar}$"

        # Usar un conjunto para evitar duplicados
        cartones_set = set()
        for carton in cartones_tuplas:
            if carton[0]:  # Evitar errores con valores vacíos o nulos
                numeros = eval(carton[0]) if isinstance(carton[0], str) else carton[0]
                if isinstance(numeros, list):
                    cartones_set.update(numeros)
                else:
                    cartones_set.add(numeros)

        # Convertir el conjunto a lista para pasar a la plantilla
        cartones = list(cartones_set)

        return render_template("disponibles_no.html", cartones=cartones, montos_totales=montos_totales)

if __name__ == '__main__':
    app.run(debug=True)
