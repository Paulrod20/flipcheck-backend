from pydantic import BaseModel

class PriceResult(BaseModel):
    source: str
    title: str
    price: float
    condition: str
    url: str
    image: str
