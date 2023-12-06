from flask import Flask, Blueprint, render_template, request, redirect, url_for
import mysql.connector
import bcrypt

app = Flask(__name__)

# Configuración de la conexión a la base de datos
def connect_to_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='tbk'
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión a la base de datos: {err}")
        return None

# Función para encriptar la contraseña
def encriptar_contraseña(contraseña):
    contraseña_codificada = contraseña.encode('utf-8')
    salt = bcrypt.gensalt()
    contraseña_encriptada = bcrypt.hashpw(contraseña_codificada, salt)
    return contraseña_encriptada

# Rutas relacionadas con el registro de usuarios
register_routes = Blueprint('register', __name__)

@register_routes.route('/register', methods=['GET', 'POST'])
def register():
    error_message = None
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        rol = 'cliente'

        # Encriptar la contraseña antes de almacenarla en la base de datos
        contraseña_encriptada = encriptar_contraseña(contrasena)

        conn = connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()
                sql_check_email = "SELECT id_usuario FROM Usuarios WHERE correo = %s"
                cursor.execute(sql_check_email, (correo,))
                existing_user = cursor.fetchone()

                if existing_user:
                    error_message = "El correo ya está registrado. Por favor, usa otro correo."
                else:
                    sql_insert_user = "INSERT INTO Usuarios (nombre, correo, contrasena, rol) VALUES (%s, %s, %s, %s)"
                    values = (nombre, correo, contraseña_encriptada, rol)
                    cursor.execute(sql_insert_user, values)
                    conn.commit()
                    cursor.close()
                    conn.close()

                    return redirect(url_for('login.login'))  # Suponiendo que 'login' es el nombre correcto de tu función de inicio de sesión
            except mysql.connector.Error as err:
                print(f"Error al insertar el usuario en la base de datos: {err}")
                error_message = "Ocurrió un error al registrar el usuario. Por favor, intenta nuevamente."
        else:
            error_message = "Error de conexión a la base de datos. Por favor, intenta nuevamente."

    return render_template('register.html', error_message=error_message)

# Agregar el Blueprint 'register_routes' a la app Flask
app.register_blueprint(register_routes)



