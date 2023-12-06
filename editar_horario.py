import mysql.connector
from flask import Blueprint, render_template, request, redirect, url_for, flash
from authentication import login_required
from db import connect_to_db
from wtforms import Form, StringField, BooleanField, SelectField
from wtforms.validators import InputRequired

editar_horario_routes = Blueprint('editar_horario', __name__)

# Create a WTForm for editing a schedule
class EditScheduleForm(Form):
    fecha = StringField('Nueva Fecha', validators=[InputRequired()])
    hora = StringField('Nueva Hora', validators=[InputRequired()])
    servicio = SelectField('Nuevo Servicio', coerce=int)
    disponibilidad = BooleanField('Nueva Disponibilidad')

# ...

# Ruta para editar un horario
@editar_horario_routes.route('/editar_horario/<int:horario_id>', methods=['GET', 'POST'])
@login_required
def editar_horario(horario_id):
    # Conectarse a la base de datos
    conn = connect_to_db()
    if not conn:
        flash("Error de conexión a la base de datos", "error")
        return redirect(url_for('admin.admin'))

    # Obtener el horario a editar desde la base de datos
    try:
        cursor = conn.cursor(dictionary=True)
        sql_get_horario = "SELECT * FROM Horarios WHERE id_horario = %s"
        cursor.execute(sql_get_horario, (horario_id,))
        horario = cursor.fetchone()
        cursor.close()
    except mysql.connector.Error as err:
        flash(f"Error al obtener el horario: {err}", "error")
        horario = None

    if not horario:
        flash("El horario no existe", "error")
        return redirect(url_for('admin.admin'))

    # Obtener los servicios desde la base de datos
    try:
        cursor = conn.cursor(dictionary=True)
        sql_get_servicios = "SELECT id_servicio, nombre FROM Servicios"
        cursor.execute(sql_get_servicios)
        servicios = cursor.fetchall()
        cursor.close()
    except mysql.connector.Error as err:
        flash(f"Error al consultar los servicios: {err}", "error")
        servicios = []

    # Crear una instancia del formulario de edición
    form = EditScheduleForm(request.form)

    # Poblar el formulario con los datos del horario
    form.fecha.data = horario['fecha']
    form.hora.data = horario['hora']
    form.servicio.choices = [(servicio['id_servicio'], servicio['nombre']) for servicio in servicios]
    form.disponibilidad.data = horario['disponibilidad']

    # Verificar si se ha enviado el formulario
    if request.method == 'POST':
        try:
            cursor = conn.cursor()

            # Obtener los nuevos valores del formulario
            form.fecha.data = request.form['fecha']
            form.hora.data = request.form['hora']
            form.servicio.data = int(request.form['servicio'])
            form.disponibilidad.data = 'disponibilidad' in request.form

            # Actualizar el horario en la base de datos
            sql_update_horario = "UPDATE Horarios SET fecha = %s, hora = %s, id_servicio = %s, disponibilidad = %s WHERE id_horario = %s"
            values = (form.fecha.data, form.hora.data, form.servicio.data, form.disponibilidad.data, horario_id)
            cursor.execute(sql_update_horario, values)
            conn.commit()

            flash("Horario actualizado correctamente", "success")
        except mysql.connector.Error as err:
            flash(f"Error en la base de datos: {err}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('admin.admin'))

    return render_template('editar_horario.html', horario=horario, form=form, servicios=servicios)