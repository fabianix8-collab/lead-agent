"""
Conector al calendario. En modo mock simula la creación del evento y
devuelve un link falso pero con el mismo formato que la API real, para
que el resto del sistema no tenga que distinguir entre modos.
"""
from datetime import datetime, timedelta


class CalendarConnector:
    def __init__(self, mock: bool = True):
        self.mock = mock

    def agendar(self, email_lead: str, asunto: str, fecha_hora_sugerida_iso: str,
                duracion_minutos: int = 30) -> dict:
        try:
            inicio = datetime.fromisoformat(fecha_hora_sugerida_iso)
        except ValueError:
            return {"status": "error", "mensaje": "fecha_hora_sugerida_iso inválida"}

        fin = inicio + timedelta(minutes=duracion_minutos)

        if self.mock:
            return {
                "status": "ok",
                "modo": "mock",
                "evento_id": f"mock-evt-{inicio.strftime('%Y%m%d%H%M')}",
                "inicio": inicio.isoformat(),
                "fin": fin.isoformat(),
                "invitado": email_lead,
                "link_simulado": f"https://calendar.mock/event/{inicio.strftime('%Y%m%d%H%M')}",
            }

        # --- Implementación real (requiere google-api-python-client) ---
        # from googleapiclient.discovery import build
        # from google.oauth2.credentials import Credentials
        # from config import Config
        # creds = Credentials.from_authorized_user_file(Config.GMAIL_CREDENTIALS_PATH)
        # service = build("calendar", "v3", credentials=creds)
        # evento = service.events().insert(
        #     calendarId=Config.GOOGLE_CALENDAR_ID,
        #     body={
        #         "summary": asunto,
        #         "start": {"dateTime": inicio.isoformat()},
        #         "end": {"dateTime": fin.isoformat()},
        #         "attendees": [{"email": email_lead}],
        #     },
        # ).execute()
        # return {"status": "ok", "modo": "real", "evento_id": evento["id"], "link": evento["htmlLink"]}
        raise NotImplementedError(
            "Instala google-api-python-client y descomenta la implementación real en calendar_google.py"
        )
