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

    def search_card(self, name: str, set_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Search for a card by name and optionally set name."""
        # Clean up the name and set name
        name = name.strip().lower()
        if set_name:
            set_name = set_name.strip()
        
        # Try different variations of the query
        queries = [
            f'name:"{name}"',  # Exact match
            f'name:"{name.replace(" ex", " ex")}"',  # Try with space before ex
            f'name:"{name.replace(" ex", "ex")}"',   # Try without space before ex
        ]
        
        if set_name:
            # Try different variations of the set name
            set_queries = [
                f' set.name:"{set_name}"',
                f' set.name:"{set_name.replace("&", "&")}"',
                f' set.name:"{set_name.replace("&", "and")}"',
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
        response = requests.get(
            f"{self.base_url}/sets",
            headers=self.headers,
            params={"q": f'name:"{set_name}"'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return data["data"][0]
        return None

    def get_card_market_price(self, card_id: str) -> Optional[float]:
        """Get the market price for a card."""
        card_data = self.get_card_by_id(card_id)
        if card_data and "data" in card_data:
            tcgplayer = card_data["data"].get("tcgplayer", {})
            if "prices" in tcgplayer:
                prices = tcgplayer["prices"]
                # Try to get the market price in this order: holofoil > normal > reverse holofoil
                if "holofoil" in prices and prices["holofoil"].get("market"):
                    return prices["holofoil"]["market"]
                elif "normal" in prices and prices["normal"].get("market"):
                    return prices["normal"]["market"]
                elif "reverseHolofoil" in prices and prices["reverseHolofoil"].get("market"):
                    return prices["reverseHolofoil"]["market"]
        return None

    def extract_card_info(self, text: str) -> Dict[str, str]:
        """Extract card information from OCR text."""
        # This is a placeholder for OCR text processing
        # In a real implementation, this would use NLP or pattern matching
        return {
            "name": "",
            "set": ""
        } 