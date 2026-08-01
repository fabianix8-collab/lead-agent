"""
Conector al CRM. En modo mock guarda los contactos en memoria/JSON local,
simulando la respuesta real de la API de Airtable, para que el resto del
sistema (y la demo) sea idéntico sin importar el modo.
"""
import json
import os
from datetime import datetime, timezone

_MOCK_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "mock_data", "crm_store.json")


class AirtableConnector:
    def __init__(self, mock: bool = True):
        self.mock = mock
        if self.mock and not os.path.exists(_MOCK_STORE_PATH):
            with open(_MOCK_STORE_PATH, "w") as f:
                json.dump([], f)

    def crear_contacto(self, nombre: str, email: str, prioridad: str,
                        empresa: str = "", notas: str = "") -> dict:
        registro = {
            "nombre": nombre,
            "email": email,
            "empresa": empresa,
            "prioridad": prioridad,
            "notas": notas,
            "creado_en": datetime.now(timezone.utc).isoformat(),
        }

        if self.mock:
            with open(_MOCK_STORE_PATH, "r") as f:
                data = json.load(f)
            registro["id"] = f"mock-rec-{len(data) + 1:04d}"
            data.append(registro)
            with open(_MOCK_STORE_PATH, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return {"status": "ok", "modo": "mock", "record_id": registro["id"]}

        from pyairtable import Api
        from config import Config

        # Mapeo explícito a los nombres de columna de Airtable (deben existir
        # tal cual en la tabla — ver README, sección "Configurar Airtable real").
        campos = {
            "Nombre": nombre,
            "Email": email,
            "Empresa": empresa,
            "Prioridad": prioridad,
            "Notas": notas,
        }

        api = Api(Config.AIRTABLE_API_KEY)
        table = api.table(Config.AIRTABLE_BASE_ID, Config.AIRTABLE_TABLE_NAME)
        record = table.create(campos)
        return {"status": "ok", "modo": "real", "record_id": record["id"]}
