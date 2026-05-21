from pydantic import BaseModel
from typing import List

class PriceResult(BaseModel):
    source: str
    price: float
    condition: str
    url: str
    
class SearchResult(BaseModel):
    title: str
    platform: str
    image: str
    prices: List[PriceResult]
    