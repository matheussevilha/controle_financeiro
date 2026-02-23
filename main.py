from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gspread
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

app = FastAPI()

# -----------------------------
# CONFIG GOOGLE SHEETS
# -----------------------------

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credenciais.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

# Nome da planilha
sheet = client.open("ControleFinanceiro").worksheet("BalançoFinanceiro")


# -----------------------------
# MODELO RECEBIDO
# -----------------------------

class Notificacao(BaseModel):
    notificacao: str


# -----------------------------
# WEBHOOK
# -----------------------------

@app.post("/webhook")
def receber_notificacao(info: Notificacao):

    texto = info.notificacao

    data = None
    valor = None
    classificacao = None
    tipo_movimento = None  # entrada ou saida

    # -----------------------------------
    # COMPRA CRÉDITO
    # -----------------------------------
    if "Compra aprovada" in texto:

        classificacao = "Credito_ITAU"
        tipo_movimento = "saida"

        valor_match = re.search(r"R\$ ?([0-9]+,[0-9]{2})", texto)
        data_match = re.search(r"em (\d{2}/\d{2}/\d{4})", texto)

        if valor_match:
            valor = float(valor_match.group(1).replace(",", "."))

        if data_match:
            data = data_match.group(1)

    # -----------------------------------
    # PIX ENVIADO
    # -----------------------------------
    elif "Você enviou" in texto:

        classificacao = "Pix_Enviado"
        tipo_movimento = "saida"

        valor_match = re.search(r"R\$ ?([0-9]+,[0-9]{2})", texto)

        if valor_match:
            valor = float(valor_match.group(1).replace(",", "."))

        data = datetime.today().strftime("%d/%m/%Y")

    # -----------------------------------
    # PIX RECEBIDO
    # -----------------------------------
    elif "Você recebeu" in texto:

        classificacao = "Pix_Recebido"
        tipo_movimento = "entrada"

        valor_match = re.search(r"R\$ ?([0-9]+,[0-9]{2})", texto)

        if valor_match:
            valor = float(valor_match.group(1).replace(",", "."))

        data = datetime.today().strftime("%d/%m/%Y")

    # -----------------------------------
    # VALIDAÇÃO
    # -----------------------------------
    if not valor:
        raise HTTPException(status_code=400, detail="Valor não identificado")

    if not data:
        data = datetime.today().strftime("%d/%m/%Y")

    # -----------------------------------
    # ENVIO PARA PLANILHA
    # -----------------------------------
    sheet.append_row([
        data,
        classificacao,
        valor,
        tipo_movimento
    ])

    return {"status": "ok"}