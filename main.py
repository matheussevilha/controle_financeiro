from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = FastAPI(title="Cost Management API")

# --------- MODEL ----------
class Gasto(BaseModel):
    data: str
    classificacao: str
    gasto: float

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

SHEET_NAME = "Controle_Gastos"
sheet = client.open(SHEET_NAME).sheet1

# --------- ENDPOINT ----------
@app.post("/webhook")
def add_cost(info: Gasto):
    try:
        sheet.append_row([
            info.data,
            info.classificacao,
            info.gasto
        ])
        return {"message": "Cost item added to Google Sheets"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
