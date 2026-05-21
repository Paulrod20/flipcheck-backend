from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from ebay import search_ebay_prices
import os

load_dotenv()

app = FastAPI()

# Allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FlipCheck API is running!"}

@app.get("/search")
async def search(query: str):
    results = await search_ebay_prices(query)
    return {"results": results}

@app.get("/debug")
def debug():
    return {
        "app_id": os.getenv("EBAY_APP_ID"),
        "cert_id": os.getenv("EBAY_CERT_ID"),
    }