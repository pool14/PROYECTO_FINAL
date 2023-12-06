# Importa las bibliotecas necesarias
import mysql.connector
from flask import Flask, render_template, redirect, url_for, session, request, flash
from functools import wraps
from db import connect_to_db
from authentication import login_required
from admin import admin_routes
from cliente import cliente_routes
from login import login_routes
from logout import logout_routes
from editar_horario import editar_horario_routes
from register import register_routes
from agendar import agendar_routes  
from cancelar import cancelar_routes  
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from flask import g

# Definir la ruta al archivo de credenciales
SERVICE_ACCOUNT_FILE = 'the-barber-king-34b38b92c3a5.json'

# Configuración de la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'elpepe'

# Configuración de Flask-Mail para enviar correos electrónicos
# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # Puerto SSL de Gmail
app.config['MAIL_USERNAME'] = 'tovinow@gmail.com'
app.config['MAIL_PASSWORD'] = 'othn ymrp nkhe gkoj'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


mail = Mail(app)

# Configuración de la API de Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'the-barber-king-34b38b92c3a5.json'  # Reemplaza con la ruta correcta

# Conecta con la base de datos
conn = connect_to_db()
cursor = conn.cursor()

# Rutas de la aplicación
app.register_blueprint(admin_routes)
app.register_blueprint(cliente_routes)
app.register_blueprint(login_routes)
app.register_blueprint(logout_routes)
app.register_blueprint(register_routes)
app.register_blueprint(editar_horario_routes)
app.register_blueprint(agendar_routes)
app.register_blueprint(cancelar_routes)

# Función para enviar correo electrónico al agendar una cita
def enviar_correo_agendado(email_cliente):
    msg = Message('Cita agendada con éxito', sender='jbraucin2005@gmail.com', recipients=[email_cliente])
    msg.body = "Su cita ha sido agendada exitosamente."
    mail.send(msg)


# Función para crear un evento en Google Calendar
def create_google_calendar_event(client_email, event_data):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    calendar_service = build('calendar', 'v3', credentials=credentials)

    # Obtén el ID del calendario del cliente (puedes guardarlo en la base de datos)
    calendar_id = 'primary'  # Puedes cambiar esto según tu estructura

    # Crea el evento
    event = calendar_service.events().insert(calendarId=calendar_id, body=event_data).execute()

    # Guarda el ID del evento en la base de datos
    # Guarda event['id'] en la base de datos para referencia futura

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para agendar una cita
@app.route('/agendar_cita', methods=['POST'])
@login_required
def agendar_cita():
    user_id = session['user_id']
    horario_id = request.form.get('horario_id')

    # Verifica si el horario seleccionado todavía está disponible
    sql_check_disponibilidad = "SELECT disponibilidad FROM Horarios WHERE id_horario = %s"
    cursor.execute(sql_check_disponibilidad, (horario_id,))
    disponibilidad_result = cursor.fetchone()

    if disponibilidad_result is not None:
        disponibilidad = disponibilidad_result[0]

        if disponibilidad == 1:  # El horario todavía está disponible
            # Actualiza la disponibilidad del horario a no disponible (0)
            sql_update_disponibilidad = "UPDATE Horarios SET disponibilidad = 0 WHERE id_horario = %s"
            cursor.execute(sql_update_disponibilidad, (horario_id,))
            conn.commit()

            # Inserta la cita en la tabla de citas (debes implementar esto según tu estructura de datos)
            sql_insert_cita = "INSERT INTO Citas (id_usuario, id_horario) VALUES (%s, %s)"
            cursor.execute(sql_insert_cita, (user_id, horario_id))
            conn.commit()

            # Envía un correo electrónico al cliente con la información de la cita
            client_email_query = "SELECT correo FROM Usuarios WHERE id_usuario = %s"
            cursor.execute(client_email_query, (user_id,))
            client_email = cursor.fetchone()[0]

            event_data = {
                'summary': 'Cita con The Barber King',
                'location': 'Ubicación de la barbería',
                'description': 'Detalles adicionales de la cita',
                'start': {'dateTime': '2023-11-19T10:00:00', 'timeZone': 'America/New_York'},
                'end': {'dateTime': '2023-11-19T11:00:00', 'timeZone': 'America/New_York'},
                'attendees': [{'email': client_email}],
            }

            create_google_calendar_event(client_email, event_data)

            flash("Cita agendada con éxito", "success")
        else:
            flash("El horario seleccionado ya no está disponible", "warning")
    else:
        flash("El horario seleccionado no existe o no está disponible", "warning")

    return redirect(url_for('cliente.cliente'))

# Función para enviar recordatorio una hora antes del servicio
def send_reminder_email(client_email, event_data):
    template = f"""
    <p>Recordatorio de Cita</p>
    <p>Fecha: {event_data['start']['dateTime']}</p>
    <p>Ubicación: {event_data['location']}</p>
    <p>Detalles: {event_data['description']}</p>
    <p>Confirma tu asistencia: [Enlace para confirmar]</p>
    """

    send_email(client_email, 'Recordatorio de Cita', template)

# Tarea programada para enviar recordatorios
def schedule_reminder_emails():
    # Obtén eventos en las próximas horas (puedes ajustar este rango según tus necesidades)
    now = datetime.utcnow()
    events = calendar_service.events().list(
        calendarId='primary',
        timeMin=now.isoformat() + 'Z',
        timeMax=(now + timedelta(hours=1)).isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    for event in events:
        # Obtén el correo del cliente desde la base de datos (asumiendo que guardaste el correo al crear el evento)
        client_email_query = "SELECT correo FROM Usuarios WHERE id_usuario = %s"
        cursor.execute(client_email_query, (user_id,))
        client_email = cursor.fetchone()[0]

        send_reminder_email(client_email, event)

# Ruta para eliminar una cita
@app.route('/eliminar_cita', methods=['POST'])
@login_required
def eliminar_cita():
    user_id = session['user_id']
    cita_id = request.form.get('cita_id')

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

    return redirect(url_for('cliente.cliente'))

# Cierre de la conexión con la base de datos
@app.teardown_appcontext
def close_db(error):
    if 'conn' in g:
        g.conn.close()

# Tarea programada para enviar recordatorios una hora antes del servicio
# Se debe configurar una tarea programada en tu servidor para ejecutar esta función periódicamente
# Por ejemplo, utilizando Celery o un cronjob.

# Comentario: Asegúrate de revisar y ajustar la configuración según tus necesidades
# Supongamos que obtienes el correo del cliente después de agendar la cita

