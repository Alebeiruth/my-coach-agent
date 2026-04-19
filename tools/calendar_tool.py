import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from langchain_core.tools import tool

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = "credentials/google_credentials.json"
TOKEN_FILE = "credentials/token_python.json"

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

@tool
def agendar_sessao(
    tipo: str,
    titulo: str,
    descricao: str,
    data_inicio: str,
    duracao_minutos: int = 60,
) -> str:
    """
    Cria um evento de estudo no Google Calendar.

    Args:
        tipo: 'leetcode' ou 'artigo'.
        titulo: Título do exercício ou artigo.
        descricao: Detalhes do que será estudado ou praticado.
        data_inicio: Data e hora no formato 'YYYY-MM-DD HH:MM'. Exemplo: '2025-04-21 08:00'.
        duracao_minutos: Duração em minutos. Padrão: 60.

    Returns:
        Link do evento criado.
    """
    try:
        service = get_calendar_service()

        emoji = "💻" if tipo == "leetcode" else "📚"
        inicio = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M")
        fim = inicio + timedelta(minutes=duracao_minutos)

        evento = {
            "summary": f"{emoji} {titulo}",
            "description": descricao,
            "start": {
                "dateTime": inicio.isoformat(),
                "timeZone": "America/Sao_Paulo",
            },
            "end": {
                "dateTime": fim.isoformat(),
                "timeZone": "America/Sao_Paulo",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [{"method": "popup", "minutes": 30}],
            },
        }

        resultado = service.events().insert(
            calendarId="primary",
            body=evento,
        ).execute()

        return f"Sessão agendada: {resultado.get('htmlLink')}"

    except Exception as e:
        return f"Erro ao agendar: {str(e)}"