from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from schemas import CardBase, CardCreate, CardResponse
from notion_integration import NotionIntegration
from pokemon_tcg_api import PokemonTCGAPI
from config import get_settings
from image_processing import process_card_image
import logging

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cards", tags=["cards"])
notion = NotionIntegration()
pokemon_tcg = PokemonTCGAPI()

def transform_card_data_for_notion(card_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Pokemon TCG API card data to match our schema."""
    return {
        "name": str(card_data["name"]),
        "collection": str(card_data.get("set", {}).get("name", "Unknown Set")),
        "market_price": float(card_data.get("market_price", 0.0)),
        "rarity": str(card_data.get("rarity", "Unknown")),
        "image_url": str(card_data.get("images", {}).get("large", "https://example.com/placeholder.jpg")),
        "variant_number": str(card_data.get("number", "")),
        "card_id": str(card_data.get("id", "")),
        "repeated": False  # This will be updated when we check if the card exists
    }

@router.get("/search", response_model=CardResponse)
async def search_card(query: str, set_id: Optional[str] = None):
    """Search for a card using the Pokemon TCG API."""
    try:
        # Search for the card
        cards = pokemon_tcg.search_card(query, set_id)
        
        if not cards:
            return CardResponse(
                success=False,
                message="No cards found",
                error="Card not found in Pokemon TCG API"
            )
        
        # Transform all cards to match our schema
        transformed_cards = [CardBase(**transform_card_data_for_notion(card)) for card in cards]
        
        return CardResponse(
            success=True,
            message="Cards found successfully",
            cards=transformed_cards
        )
        
    except Exception as e:
        logger.error(f"Error searching for card: {str(e)}")
        return CardResponse(
            success=False,
            message="Error searching for card",
            error=str(e)
        )

@router.post("/upload", response_model=CardResponse)
async def upload_card(file: UploadFile = File(...)):
    """Upload and process a card image."""
    try:
        # Process the image
        result = await process_card_image(file)
        
        if not result["success"]:
            return CardResponse(
                success=False,
                message="Error processing image",
                error=result["error"]
            )
        
        # Search for the card using the extracted text
        cards = pokemon_tcg.search_card(result["text"])
        
        if not cards:
            return CardResponse(
                success=False,
                message="No cards found",
                error="Card not found in Pokemon TCG API"
            )
        
        # Transform all cards to match our schema
        transformed_cards = [CardBase(**transform_card_data_for_notion(card)) for card in cards]
        
        return CardResponse(
            success=True,
            message="Cards processed successfully",
            cards=transformed_cards
        )
        
    except Exception as e:
        logger.error(f"Error processing card image: {str(e)}")
        return CardResponse(
            success=False,
            message="Error processing card image",
            error=str(e)
        )

@router.post("/prompt", response_model=CardResponse)
async def create_card(card: CardCreate):
    """Create a card entry manually."""
    # Search for card in Pokemon TCG API
    cards = pokemon_tcg.search_card(card.name)
    if not cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found in Pokemon TCG API"
        )
    
    # Use the first matching card and transform it
    card_data = transform_card_data_for_notion(cards[0])
    
    try:
        # Create Notion report
        notion_page_id = notion.create_card_report(card_data)
        if not notion_page_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Notion report"
            )
        
        return CardResponse(
            success=True,
            message="Card created successfully",
            card=card_data
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create card: {str(e)}"
        )

@router.post("/report", response_model=CardResponse)
async def create_card_report(query: str, set_id: str, group_id: str):
    """Create a Notion report for cards matching the search query."""
    try:
        # Search for cards
        cards = pokemon_tcg.search_card(query, set_id)
        if not cards:
            return CardResponse(
                success=False,
                message="No cards found",
                cards=None,
                error="No cards found matching the search criteria"
            )
        
        transformed_cards = []
        created_cards = 0
        repeated_cards = 0
        
        # Transform and create reports for each card
        for card in cards:
            # Check if card already exists
            exists = notion.check_existing_card(card["id"])
            
            # Transform card data
            transformed_card = transform_card_data_for_notion(card)
            transformed_card["repeated"] = exists
            transformed_card["group_id"] = group_id  # Set the group_id to indicate these cards are grouped together
            
            if exists:
                repeated_cards += 1
            
            # Create Notion report for all cards
            try:
                page_id = notion.create_card_report(transformed_card, method="Manual", group_id=group_id)
                if page_id:
                    created_cards += 1
                    transformed_cards.append(transformed_card)
            except Exception as e:
                logger.error(f"Error creating Notion report for card {card['id']}: {str(e)}")
                continue
        
        message = f"Successfully added {created_cards} cards to Notion"
        if repeated_cards > 0:
            message += f" ({repeated_cards} repeated cards)"
        
        return CardResponse(
            success=True,
            message=message,
            cards=transformed_cards
        )
            
    except Exception as e:
        logger.error(f"Error creating card report: {str(e)}")
        return CardResponse(
            success=False,
            message="Error creating card report",
            cards=None,
            error=str(e)
        ) 