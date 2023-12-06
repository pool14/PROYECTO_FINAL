from flask import Blueprint, render_template, request, redirect, url_for, session
from db import connect_to_db
import bcrypt

login_routes = Blueprint('login', __name__)

@login_routes.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        conn = connect_to_db()
        if conn:
            cursor = conn.cursor()
            try:
                sql = "SELECT id_usuario, nombre, contrasena, rol FROM Usuarios WHERE correo = %s"
                cursor.execute(sql, (correo,))
                user = cursor.fetchone()

                if user:
                    stored_password = user[2]
                    if user[3] == 'administrador' or bcrypt.checkpw(contrasena.encode('utf-8'), stored_password.encode('utf-8')):
                        session['user_id'] = user[0]
                        session['user_name'] = user[1]
                        session['user_role'] = user[3]

                        if user[3] == 'administrador':
                            cursor.close()
                            conn.close()
                            return redirect(url_for('admin.admin'))
                        else:
                            cursor.close()
                            conn.close()
                            return redirect(url_for('cliente.cliente'))
                    else:
                        error_message = "Credenciales inválidas. Por favor, intenta nuevamente."
                else:
                    error_message = "Usuario no encontrado. Por favor, registra una cuenta primero."

            except Exception as e:
                print(f"Error al autenticar al usuario: {e}")
                error_message = "Ocurrió un error al iniciar sesión. Por favor, intenta nuevamente."

            finally:
                cursor.close()
                conn.close()

    return render_template('login.html', error_message=error_message)
