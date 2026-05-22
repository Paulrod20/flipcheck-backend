import httpx
import re
from fastapi import HTTPException
from auth import get_ebay_access_token
from models import PriceResult


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def _console_patterns(normalized_query: str) -> list[str]:
    patterns: list[str] = []

    ps_match = re.search(r"\b(?:playstation|ps)\s*([1-5])\b", normalized_query)
    if ps_match:
        generation = ps_match.group(1)
        patterns.append(rf"\b(?:playstation|play\s*station|ps)\s*{generation}\b")

    xbox_one_match = re.search(r"\bxbox\s*one\s*([xs])\b", normalized_query)
    if xbox_one_match:
        model = xbox_one_match.group(1)
        patterns.append(rf"\bxbox\s*one\s*{model}\b")

    xbox_series_match = re.search(r"\bxbox\s*series\s*([xs])\b", normalized_query)
    if xbox_series_match:
        model = xbox_series_match.group(1)
        patterns.append(rf"\bxbox\s*series\s*{model}\b")

    if re.search(r"\bxbox\s*360\b", normalized_query):
        patterns.append(r"\bxbox\s*360\b")

    if re.search(r"\b(?:nintendo\s*64|n64)\b", normalized_query):
        patterns.append(r"\b(?:nintendo\s*64|n64)\b")

    return patterns


def _is_title_match(query: str, title: str) -> bool:
    normalized_query = _normalize_text(query)
    normalized_title = _normalize_text(title)

    if not normalized_query:
        return False

    if normalized_query in normalized_title:
        return True

    patterns = _console_patterns(normalized_query)
    if patterns:
        return all(re.search(pattern, normalized_title) for pattern in patterns)

    title_tokens = set(normalized_title.split())
    query_tokens = normalized_query.split()
    return all(token in title_tokens for token in query_tokens)

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
                    "q": f'"{query}"',
                    "limit": 50,
                    "filter": "buyingOptions:{FIXED_PRICE},conditions:{USED}",
                    "category_ids": "139973",
                    "sort": "relevance",
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
        title = item.get("title", "")
        if not _is_title_match(query, title):
            continue
        price = item.get("price", {})
        try:
            price_value = float(price.get("value", 0))
        except (TypeError, ValueError) as e:
            raise HTTPException(status_code=502, detail=f"Unexpected price format from eBay: {e}")
        results.append(PriceResult(
            source="eBay",
            title=title,
            price=price_value,
            condition=item.get("condition", "Unknown"),
            url=item.get("itemWebUrl", "#"),
            image=item.get("image", {}).get("imageUrl", ""),
        ))

    return results[:10]