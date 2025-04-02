import requests
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class PokemonTCGAPI:
    def __init__(self):
        self.api_key = os.getenv("POKEMON_TCG_API_KEY")
        self.base_url = "https://api.pokemontcg.io/v2"
        self.headers = {"X-Api-Key": self.api_key} if self.api_key else {}

    def transform_card_name(self, name: str) -> str:
        """Transform card name according to Pokemon TCG API conventions."""
        name = name.strip().lower()
        # Handle EX cards
        if name.endswith(" ex"):
            return name.replace(" ex", "-ex")
        return name

    def transform_set_name(self, set_name: str) -> str:
        """Transform set name according to Pokemon TCG API conventions."""
        set_name = set_name.strip()
        # Handle Scarlet & Violet sets
        if "scarlet & violet" in set_name.lower():
            # Extract expansion name if present
            parts = set_name.split("-")
            if len(parts) > 1:
                return parts[1].strip()
            return "Scarlet & Violet"
        return set_name

    def search_card(self, name: str, set_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Search for a card by name and optionally set name."""
        # Transform the name and set name
        transformed_name = self.transform_card_name(name)
        transformed_set = self.transform_set_name(set_name) if set_name else None
        
        # Try different variations of the query
        queries = [
            f'name:"{transformed_name}"',  # Exact match
        ]
        
        if transformed_set:
            # Try different variations of the set name
            set_queries = [
                f' set.name:"{transformed_set}"',
                f' set.name:"{transformed_set.replace("&", "&")}"',
                f' set.name:"{transformed_set.replace("&", "and")}"',
            ]
            queries = [q + sq for q in queries for sq in set_queries]
        
        for query in queries:
            print(f"Trying query: {query}")  # Debug print
            response = requests.get(
                f"{self.base_url}/cards",
                headers=self.headers,
                params={"q": query}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    print(f"Found card with query: {query}")  # Debug print
                    return data["data"][0]
                else:
                    print(f"No results found for query: {query}")  # Debug print
        
        print(f"No card found with any query variation")  # Debug print
        return None

    def get_card_by_id(self, card_id: str) -> Optional[Dict[str, Any]]:
        """Get card details by ID."""
        response = requests.get(
            f"{self.base_url}/cards/{card_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None

    def get_set_by_name(self, set_name: str) -> Optional[Dict[str, Any]]:
        """Get set information by name."""
        transformed_set = self.transform_set_name(set_name)
        response = requests.get(
            f"{self.base_url}/sets",
            headers=self.headers,
            params={"q": f'name:"{transformed_set}"'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return data["data"][0]
        return None

    def get_card_market_price(self, card_id: str) -> Optional[float]:
        """Get the market price for a card using cardmarket data."""
        card_data = self.get_card_by_id(card_id)
        if card_data and "data" in card_data:
            cardmarket = card_data["data"].get("cardmarket", {})
            if "prices" in cardmarket:
                prices = cardmarket["prices"]
                # Use averageSellPrice from cardmarket
                if "averageSellPrice" in prices:
                    return prices["averageSellPrice"]
        return None

    def extract_card_info(self, text: str) -> Dict[str, str]:
        """Extract card information from OCR text."""
        # This is a placeholder for OCR text processing
        # In a real implementation, this would use NLP or pattern matching
        return {
            "name": "",
            "set": ""
        } 