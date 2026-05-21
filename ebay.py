import httpx
from fastapi import HTTPException
from auth import get_ebay_access_token

async def search_ebay_prices(query: str):
    try:
        token = await get_ebay_access_token()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to obtain eBay access token: {e}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers={
                    "Authorization": f"Bearer {token}",
                },
                params={
                    "q": query,
                    "limit": 10,
                    "filter": "buyingOptions:{FIXED_PRICE},conditions:{USED}",
                }
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"eBay API error {e.response.status_code}: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error reaching eBay API: {e}")

    results = []
    items = data.get("itemSummaries", [])

    for item in items:
        price = item.get("price", {})
        try:
            price_value = float(price.get("value", 0))
        except (TypeError, ValueError) as e:
            raise HTTPException(status_code=502, detail=f"Unexpected price format from eBay: {e}")
        results.append({
            "source": "eBay",
            "title": item.get("title", ""),
            "price": price_value,
            "condition": item.get("condition", "Unknown"),
            "url": item.get("itemWebUrl", "#"),
            "image": item.get("image", {}).get("imageUrl", ""),
        })

    return results
