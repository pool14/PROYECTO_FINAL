from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from db import connect_to_db

# Crear un Blueprint para las rutas de agendar
agendar_routes = Blueprint('agendar', __name__)

@agendar_routes.route('/confirmar_cita/<cita_id>', methods=['GET', 'POST'])
def confirmar_cita(cita_id):
    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        try:
            # Obtener detalles de la cita usando su ID
            sql_obtener_cita = "SELECT h.fecha, h.hora, s.nombre " \
                               "FROM Citas c " \
                               "JOIN Horarios h ON c.id_horario = h.id_horario " \
                               "JOIN Servicios s ON h.id_servicio = s.id_servicio " \
                               "WHERE c.id_cita = %s"
            cursor.execute(sql_obtener_cita, (cita_id,))
            cita_info = cursor.fetchone()

            if cita_info:
                fecha = cita_info[0]
                hora = cita_info[1]
                servicio = cita_info[2]

                # Simulación de mensaje flash en caso de éxito (para propósitos de demostración)
                if request.method == 'POST':
                    flash('La cita ha sido confirmada con éxito', 'success')
                    return redirect(url_for('cliente.cliente', cita_id=cita_id))

                return render_template('agendar.html', cita_id=cita_id, fecha=fecha, hora=hora, servicio=servicio)
            else:
                flash('La cita no existe', 'error')
        except Exception as e:
            print("Error:", str(e))
            flash(f"Error al obtener los detalles de la cita: {str(e)}", 'error')
        finally:
            cursor.close()
            conn.close()
    else:
        flash('Error de conexión a la base de datos', 'error')

    return render_template('agendar.html', cita_id=cita_id)
