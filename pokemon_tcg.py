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
        query = f'name:"{name}"'
        if set_name:
            query += f' set.name:"{set_name}"'
        
        response = requests.get(
            f"{self.base_url}/cards",
            headers=self.headers,
            params={"q": query}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                return data["data"][0]
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
        """Get card market price from TCGPlayer."""
        response = requests.get(
            f"{self.base_url}/cards/{card_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            cardmarket = data.get("cardmarket", {})
            if cardmarket:
                return float(cardmarket.get("prices", {}).get("averageSellPrice", 0))
        return None

    def extract_card_info(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract card information from OCR text."""
        # This is a basic implementation - you'll need to enhance it
        # based on your specific OCR results format
        lines = text.split('\n')
        card_info = {
            "name": None,
            "set": None,
            "rarity": None
        }
        
        for line in lines:
            line = line.strip()
            if not card_info["name"] and len(line) > 0:
                card_info["name"] = line
            elif "Set:" in line:
                card_info["set"] = line.replace("Set:", "").strip()
            elif any(rarity in line.lower() for rarity in ["common", "uncommon", "rare", "ultra rare"]):
                card_info["rarity"] = line.strip()
        
        return card_info if card_info["name"] else None 