# Suponiendo que tienes un archivo authentication.py que contiene las funciones necesarias para la autenticación (login_required).

from flask import Blueprint, session, flash, redirect, url_for, request, render_template
from authentication import login_required
from db import connect_to_db

cancelar_routes = Blueprint('cancelar', __name__)

@cancelar_routes.route('/cancelar_cita', methods=['GET', 'POST'])
@login_required
def cancelar_cita():
    user_id = session['user_id']
    cita_id = request.form.get('cita_id')

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        try:
            sql_get_horario_id = "SELECT id_horario FROM Citas WHERE id_cita = %s AND id_usuario = %s"
            cursor.execute(sql_get_horario_id, (cita_id, user_id))
            row = cursor.fetchone()

            if row:
                horario_id = row[0]

                sql_update_disponibilidad = "UPDATE Horarios SET disponibilidad = 1 WHERE id_horario = %s"
                cursor.execute(sql_update_disponibilidad, (horario_id,))
                conn.commit()

                sql_eliminar_cita = "DELETE FROM Citas WHERE id_cita = %s AND id_usuario = %s"
                cursor.execute(sql_eliminar_cita, (cita_id, user_id))
                conn.commit()

                flash("Cita cancelada con éxito", "success")
            else:
                flash("No se encontró información de la cita o no tienes permiso para cancelarla", "error")
        except Exception as e:
            flash(f"Error al cancelar la cita: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

    return render_template('cancelar.html', cita_id=cita_id)

    
