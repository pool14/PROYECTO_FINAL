# admin.py
import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response
from authentication import login_required
from db import connect_to_db

admin_routes = Blueprint('admin', __name__)

@admin_routes.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    # Verificar si el usuario está autenticado
    if 'user_id' not in session:
        return redirect(url_for('login.login'))

    error_message = None
    success_message = None
    servicios = []

    if request.method == 'POST':
        # Obtener los datos del formulario de agregar horario de cita
        fecha = request.form['fecha']
        hora = request.form['hora']
        id_servicio = int(request.form.get('servicio')) if request.form.get('servicio') else None
        disponibilidad = request.form.get('disponibilidad') == 'True' if request.form.get('disponibilidad') else True

        # Conectarse a la base de datos
        conn = connect_to_db()
        if conn:
            try:
                cursor = conn.cursor()

                # Verificar si el horario ya existe en la base de datos
                sql_check_horario = "SELECT COUNT(*) FROM Horarios WHERE fecha = %s AND hora = %s AND id_servicio = %s"
                cursor.execute(sql_check_horario, (fecha, hora, id_servicio))
                count = cursor.fetchone()[0]

                if count > 0:
                    flash("El horario ya existe y no se puede repetir", "error")

                else:
                    # Insertar el nuevo horario de cita en la base de datos
                    sql_insert_horario = "INSERT INTO Horarios (id_servicio, fecha, hora, disponibilidad) VALUES (%s, %s, %s, %s)"
                    values = (id_servicio, fecha, hora, disponibilidad)
                    cursor.execute(sql_insert_horario, values)
                    conn.commit()
                    cursor.close()
                    conn.close()

                    session['temp_success_message'] = "Horario Actualizado Correctamente"
            except mysql.connector.Error as err:
                error_message = f"Error al agregar el horario de cita: {err}"
        else:
            error_message = "Error de conexión a la base de datos"

    # Obtener los servicios desde la base de datos
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            sql_get_servicios = "SELECT * FROM Servicios"
            cursor.execute(sql_get_servicios)
            servicios = cursor.fetchall()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            error_message = f"Error al consultar los servicios: {err}"
            servicios = []
    else:
        error_message = "Error de conexión a la base de datos"
        servicios = []

    # Obtener los horarios de cita desde la base de datos
    conn = connect_to_db()
    if conn:
        try:
            cursor = conn.cursor()
            sql_get_horarios = "SELECT Horarios.*, Servicios.nombre AS nombre_servicio FROM Horarios INNER JOIN Servicios ON Horarios.id_servicio = Servicios.id_servicio"
            cursor.execute(sql_get_horarios)
            horarios = cursor.fetchall()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            error_message = f"Error al consultar los horarios de cita: {err}"
            horarios = []
    else:
        error_message = "Error de conexión a la base de datos"
        horarios = []

    # Renderizar la plantilla y Eliminar memoria cache del navegador para cierre de sesion
    rendered_template = render_template('admin.html', error_message=error_message, success_message=success_message, horarios=horarios, servicios=servicios)
    response = Response(rendered_template)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Ruta para eliminar un horario
@admin_routes.route('/eliminar_horario/<int:horario_id>', methods=['POST'])
def eliminar_horario(horario_id):
    # Conectarse a la base de datos
    conn = connect_to_db()
    if not conn:
        flash("Error de conexión a la base de datos", "error")
    else:
        try:
            cursor = conn.cursor()

            # Eliminar el horario de cita de la base de datos
            sql_delete_horario = "DELETE FROM Horarios WHERE id_horario = %s"
            cursor.execute(sql_delete_horario, (horario_id,))
            conn.commit()

            flash("Horario eliminado correctamente", "success")

        except mysql.connector.Error as err:
            flash(f"Error en la base de datos: {err}", "error")
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('admin.admin'))
