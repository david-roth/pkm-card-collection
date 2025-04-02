from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

class CardBase(BaseModel):
    name: str = Field(..., min_length=1)
    collection: str = Field(..., min_length=1)
    market_price: float = Field(..., ge=0)
    rarity: str = Field(..., min_length=1)
    image_url: HttpUrl
    group_id: Optional[str] = None
    variant_number: Optional[str] = None
    card_id: Optional[str] = None
    repeated: bool = False  # Flag to indicate if this card is repeated in Notion

class CardCreate(CardBase):
    pass

class CardResponse(BaseModel):
    success: bool
    message: str
    cards: Optional[List[CardBase]] = None
    error: Optional[str] = None 