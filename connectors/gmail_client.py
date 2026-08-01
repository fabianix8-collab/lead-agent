"""
Conector de ingesta. En modo mock lee de mock_data/sample_leads.json en
vez de la API de Gmail — mismo formato de salida en ambos modos.
"""
import json
import os

_SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "mock_data", "sample_leads.json")


class GmailConnector:
    def __init__(self, mock: bool = True):
        self.mock = mock

    def obtener_leads_nuevos(self) -> list[dict]:
        if self.mock:
            with open(_SAMPLE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        # --- Implementación real (requiere google-api-python-client) ---
        # from googleapiclient.discovery import build
        # from google.oauth2.credentials import Credentials
        # from config import Config
        # creds = Credentials.from_authorized_user_file(Config.GMAIL_CREDENTIALS_PATH)
        # service = build("gmail", "v1", credentials=creds)
        # results = service.users().messages().list(userId="me", q="is:unread label:leads").execute()
        # ... parsear mensajes a la misma estructura que sample_leads.json ...
        raise NotImplementedError(
            "Instala google-api-python-client y descomenta la implementación real en gmail_client.py"
        )
