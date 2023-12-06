# credentials.py
from google.oauth2 import service_account

def load_google_credentials():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            'ruta/a/tu/archivo-credenciales.json',
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        return credentials
    except Exception as e:
        print(f"Error al cargar las credenciales: {str(e)}")
        return None
