from datetime import datetime  # Agrega esta línea para importar datetime
from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from authentication import login_required
from db import connect_to_db
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from flask_mail import Message, Mail
from flask import url_for
from flask import render_template_string



# Ruta al archivo de credenciales
SERVICE_ACCOUNT_FILE = 'the-barber-king-34b38b92c3a5.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Definición de las rutas del cliente
cliente_routes = Blueprint('cliente', __name__)
mail = Mail()

@cliente_routes.route('/cliente')
@login_required
def cliente():
    user_id = session['user_id']
    conn = connect_to_db()

    # Agrega este print para verificar la ruta del archivo de credenciales
    print("Ruta completa al archivo de credenciales:", SERVICE_ACCOUNT_FILE)

    if conn:
        cursor = conn.cursor()

        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        # Obtener el servicio de la API de Google Calendar
        service = build('calendar', 'v3', credentials=credentials)

        # Obtener los eventos del calendario
        events = service.events().list(
            calendarId='calendar-service-accoun@the-barber-king.iam.gserviceaccount.com',
            timeMin='2023-01-01T00:00:00Z',
            timeMax='2023-12-31T23:59:59Z'
        ).execute()

        for event in events['items']:
            print(event['summary'])

        # Consulta los horarios disponibles para agendar
        sql = "SELECT h.id_horario, s.nombre, h.fecha, h.hora, h.disponibilidad FROM Horarios h JOIN Servicios s ON h.id_servicio = s.id_servicio WHERE h.disponibilidad = 1"
        cursor.execute(sql)
        horarios_disponibles = cursor.fetchall()

        # Consulta las citas agendadas por el usuario
        sql_citas_agendadas = "SELECT c.id_cita, s.nombre, h.fecha, h.hora FROM Citas c JOIN Horarios h ON c.id_horario = h.id_horario JOIN Servicios s ON h.id_servicio = s.id_servicio WHERE c.id_usuario = %s"
        cursor.execute(sql_citas_agendadas, (user_id,))
        citas_agendadas = cursor.fetchall()

        cursor.close()
        conn.close()

        if 'cita_agendada' in session:
            enviar_correo_agendado()
            flash("Cita agendada con éxito", "success")
            del session['cita_agendada']

        return render_template('cliente.html', horarios_disponibles=horarios_disponibles, citas_agendadas=citas_agendadas)
    else:
        return "Error de conexión a la base de datos"



def enviar_correo_agendado(cliente_nombre, user_email, fecha_cita, hora_cita, servicio_agendado, cita_id):
    try:
        confirmar_link = url_for('agendar.confirmar_cita', cita_id=cita_id, _external=True)  # Enlace para confirmar la cita
        cliente_link = url_for('cliente.cliente', _external=True)  # Enlace para llevar al cliente

        confirmar_html = render_template_string(f'<a href="{confirmar_link}">Confirmar Cita</a>')
        cliente_html = render_template_string(f'<a href="{cliente_link}">Cancela la cita</a>')

        msg = Message('Cita Agendada', sender='tovinow@gmail.com', recipients=[user_email])
        msg.html = f'''
            <p>Estimado/a {cliente_nombre},</p>
            <p>Su cita para el servicio de <strong>{servicio_agendado}</strong> ha sido agendada con éxito para el día {fecha_cita} a las {hora_cita}.</p>
            <p>Por favor, seleccione una de las siguientes opciones:</p>
            <p>{confirmar_html}</p>
            <p>{cliente_html}</p>
        '''
        mail.send(msg)
        print(f"Correo enviado con éxito a: {user_email}")
    except Exception as e:
        print("Error al enviar correo:", str(e))


@cliente_routes.route('/agendar_cita', methods=['POST'])
@login_required
def agendar_cita():
    user_id = session['user_id']
    horario_id = request.form.get('horario_id')

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        try:
            # Obtener disponibilidad, fecha, hora y el nombre del servicio del horario
            sql_check_disponibilidad = "SELECT h.disponibilidad, h.fecha, h.hora, s.nombre " \
                                       "FROM Horarios h " \
                                       "JOIN Servicios s ON h.id_servicio = s.id_servicio " \
                                       "WHERE h.id_horario = %s"
            cursor.execute(sql_check_disponibilidad, (horario_id,))
            horario_info = cursor.fetchone()

            if horario_info is not None:
                disponibilidad = horario_info[0]
                fecha_cita = horario_info[1]
                hora_cita = horario_info[2]
                servicio_agendado = horario_info[3]

                if disponibilidad == 1 and fecha_cita and hora_cita:
                    sql_update_disponibilidad = "UPDATE Horarios SET disponibilidad = 0 WHERE id_horario = %s"
                    cursor.execute(sql_update_disponibilidad, (horario_id,))
                    conn.commit()

                    sql_insert_cita = "INSERT INTO Citas (id_usuario, id_horario) VALUES (%s, %s)"
                    cursor.execute(sql_insert_cita, (user_id, horario_id))
                    conn.commit()

                    # Obtener el ID de la cita recién creada
                    cita_id = cursor.lastrowid

                    sql_obtener_usuario = "SELECT nombre, correo FROM Usuarios WHERE id_usuario = %s"
                    cursor.execute(sql_obtener_usuario, (user_id,))
                    usuario_info = cursor.fetchone()

                    if usuario_info:
                        cliente_nombre = usuario_info[0]
                        user_email = usuario_info[1]
                        # Pasar cita_id a enviar_correo_agendado
                        enviar_correo_agendado(cliente_nombre, user_email, fecha_cita, hora_cita, servicio_agendado, cita_id)
                        flash("Cita agendada con éxito", "success")
                    else:
                        flash("No se pudo obtener la información del usuario", "error")
                else:
                    flash("El horario seleccionado ya no está disponible", "warning")
            else:
                flash("El horario seleccionado no existe o no está disponible", "warning")
        except Exception as e:
            flash(f"Error al agendar la cita: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()
    else:
        flash("Error de conexión a la base de datos", "error")

    return redirect(url_for('cliente.cliente'))



@cliente_routes.route('/eliminar_cita', methods=['POST'])
@login_required
def eliminar_cita():
    user_id = session['user_id']
    cita_id = request.form.get('cita_id')

    conn = connect_to_db()
    if conn:
        cursor = conn.cursor()
        try:
            # Obtén el ID del horario de la cita
            sql_get_horario_id = "SELECT id_horario FROM Citas WHERE id_cita = %s"
            cursor.execute(sql_get_horario_id, (cita_id,))
            horario_id = cursor.fetchone()[0]

            # Actualiza la disponibilidad del horario a disponible (1)
            sql_update_disponibilidad = "UPDATE Horarios SET disponibilidad = 1 WHERE id_horario = %s"
            cursor.execute(sql_update_disponibilidad, (horario_id,))
            conn.commit()

            # Elimina la cita
            sql_eliminar_cita = "DELETE FROM Citas WHERE id_cita = %s AND id_usuario = %s"
            cursor.execute(sql_eliminar_cita, (cita_id, user_id))
            conn.commit()

            flash("Cita eliminada con éxito", "success")
        except Exception as e:
            flash(f"Error al eliminar la cita: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('cliente.cliente'))


