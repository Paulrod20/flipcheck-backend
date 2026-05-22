from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from dotenv import load_dotenv
from ebay import search_ebay_prices
from models import PriceResult
from typing import List
import httpx
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

@app.get("/search", response_model=List[PriceResult])
async def search(query: str):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    results = await search_ebay_prices(query)
    return results

@app.get("/image-proxy")
async def image_proxy(url: str = Query(...)):
    allowed_hosts = ("i.ebayimg.com",)
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname not in allowed_hosts:
        raise HTTPException(status_code=400, detail="URL not allowed")
    async with httpx.AsyncClient() as client:
        r = await client.get(url, follow_redirects=True)
        r.raise_for_status()
    return Response(content=r.content, media_type=r.headers.get("content-type", "image/jpeg"))

