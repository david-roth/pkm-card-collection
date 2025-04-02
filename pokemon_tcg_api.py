import requests
from config import get_settings
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class PokemonTCGAPI:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.POKEMON_TCG_API_KEY
        self.base_url = "https://api.pokemontcg.io/v2"
        self.headers = {"X-Api-Key": self.api_key} if self.api_key else {}

    def search_card(self, name: str, set_id: str = None) -> List[Dict[str, Any]]:
        """Search for a card by name and optionally set ID."""
        try:
            # Build query
            query = f'name:"{name}"'
            if set_id:
                query += f' set.id:"{set_id}"'

            # Make API request
            response = requests.get(
                f"{self.base_url}/cards",
                headers=self.headers,
                params={"q": query}
            )
            response.raise_for_status()

            # Process response
            data = response.json()
            cards = data.get("data", [])
            
            if not cards:
                logger.warning(f"No cards found for query: {query}")
                return []

            # Transform card data
            processed_cards = []
            for card in cards:
                processed_card = {
                    "id": card["id"],
                    "name": card["name"],
                    "set": {
                        "name": card["set"]["name"],
                        "id": card["set"]["id"]
                    },
                    "rarity": card.get("rarity", "Unknown"),
                    "number": card.get("number", ""),
                    "market_price": self.get_card_market_price(card["id"]),
                    "images": card.get("images", {
                        "small": "https://example.com/placeholder.jpg",
                        "large": "https://example.com/placeholder.jpg"
                    })
                }
                processed_cards.append(processed_card)

            return processed_cards

        except Exception as e:
            logger.error(f"Error searching for card: {str(e)}")
            return []

    def get_card_market_price(self, card_id: str) -> float:
        """Get the market price for a card."""
        try:
            response = requests.get(
                f"{self.base_url}/cards/{card_id}",
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            card = data.get("data", {})
            prices = card.get("cardmarket", {}).get("prices", {})
            
            # Try to get the average price, fall back to trending price
            price = prices.get("averageSellPrice", prices.get("trendPrice", 0.0))
            return float(price)

        except Exception as e:
            logger.error(f"Error getting card price: {str(e)}")
            return 0.0 