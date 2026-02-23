from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gspread
import os
import json
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

app = FastAPI()

# --------- GOOGLE SHEETS CONFIG ----------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_json = os.getenv("GOOGLE_CREDENTIALS")

if not creds_json:
    raise Exception("GOOGLE_CREDENTIALS not configured")

creds_dict = json.loads(creds_json)

credentials = Credentials.from_service_account_info(
    creds_dict,
    scopes=scope
)

client = gspread.authorize(credentials)

SHEET_ID = os.getenv("ID_DA_PLANILHA")

if not SHEET_ID:
    raise Exception("ID_DA_PLANILHA not configured")

sheet = client.open_by_key(SHEET_ID).worksheet("BalançoFinanceiro")


# --------- MODELO ----------
class Notificacao(BaseModel):
    notificacao: str


# --------- WEBHOOK ----------
@app.post("/webhook")
def receber_notificacao(info: Notificacao):

    texto = info.notificacao

    data = None
    valor = None
    classificacao = None
    tipo_movimento = None  # entrada ou saida

    # -------------------------
    # COMPRA CRÉDITO
    # -------------------------
    if "Compra aprovada" in texto:

        classificacao = "Credito_ITAU"
        tipo_movimento = "saida"

        valor_match = re.search(r"R\$ ?([0-9]+,[0-9]{2})", texto)
        data_match = re.search(r"em (\d{2}/\d{2}/\d{4})", texto)

        if valor_match:
            valor = float(valor_match.group(1).replace(",", "."))

        if data_match:
            data = data_match.group(1)

    # -------------------------
    # PIX ENVIADO
    # -------------------------
    elif "Você enviou" in texto:

        classificacao = "Pix_Enviado"
        tipo_movimento = "saida"

        valor_match = re.search(r"R\$ ?([0-9]+,[0-9]{2})", texto)

        if valor_match:
            valor = float(valor_match.group(1).replace(",", "."))

        data = datetime.today().strftime("%d/%m/%Y")

    # -------------------------
    # PIX RECEBIDO
    # -------------------------
    elif "Você recebeu" in texto:

        classificacao = "Pix_Recebido"
        tipo_movimento = "entrada"

        valor_match = re.search(r"R\$ ?([0-9]+,[0-9]{2})", texto)

        if valor_match:
            valor = float(valor_match.group(1).replace(",", "."))

        data = datetime.today().strftime("%d/%m/%Y")

    # -------------------------
    # VALIDAÇÃO
    # -------------------------
    if not valor:
        raise HTTPException(status_code=400, detail="Valor não identificado")

    if not data:
        data = datetime.today().strftime("%d/%m/%Y")

    # -------------------------
    # ENVIO PARA PLANILHA
    # -------------------------
    sheet.append_row([
        data,
        classificacao,
        valor,
        tipo_movimento
    ])

    return {"status": "ok"}