from notion_client import Client
from config import get_settings
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def verify_database(database_id: str) -> None:
    """Verify that the Notion database exists and has the correct structure."""
    integration = NotionIntegration()
    integration.verify_database()

class NotionIntegration:
    def __init__(self):
        settings = get_settings()
        self.client = Client(auth=settings.NOTION_TOKEN)
        self.database_id = settings.NOTION_DATABASE_ID
        self.verify_database()

    def verify_database(self) -> None:
        """Verify that the Notion database exists and has the correct structure."""
        try:
            # Try to retrieve the database
            database = self.client.databases.retrieve(self.database_id)
            logger.info(f"Successfully connected to Notion database: {database['title'][0]['text']['content']}")
            
            # Check required properties
            required_properties = {
                "Name": "title",
                "Set": "rich_text",
                "Rarity": "rich_text",
                "Market Price": "number",
                "Method": "rich_text",
                "Card Image": "url",
                "Group ID": "rich_text",
                "Variant Number": "rich_text",
                "Created Date": "date",
                "Card ID": "rich_text",
                "Repeated": "checkbox"
            }
            
            # Get actual properties
            actual_properties = database["properties"]
            
            # Check each required property and create if missing
            for prop_name, prop_type in required_properties.items():
                if prop_name not in actual_properties:
                    logger.info(f"Creating missing property: {prop_name}")
                    try:
                        self.client.databases.update(
                            database_id=self.database_id,
                            properties={
                                prop_name: {
                                    "type": prop_type,
                                    prop_type: {}  # Empty configuration for the property type
                                }
                            }
                        )
                        logger.info(f"Successfully created property: {prop_name}")
                    except Exception as e:
                        logger.error(f"Failed to create property {prop_name}: {str(e)}")
                elif actual_properties[prop_name]["type"] != prop_type:
                    logger.warning(f"Property {prop_name} has incorrect type. Expected {prop_type}, got {actual_properties[prop_name]['type']}")
            
            logger.info("Database structure verification completed")
            
        except Exception as e:
            logger.error(f"Error verifying database: {str(e)}")
            logger.error(f"Database ID: {self.database_id}")
            logger.error(f"Exception type: {type(e)}")

    def check_existing_card(self, card_id: str) -> bool:
        """Check if a card with the given ID already exists in the database."""
        try:
            # Query the database for the card ID
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Card ID",
                    "rich_text": {
                        "equals": card_id
                    }
                }
            )
            
            # If we found any results, the card exists
            return len(response["results"]) > 0
            
        except Exception as e:
            logger.error(f"Error checking for existing card: {str(e)}")
            return False

    def create_card_report(self, card_data: Dict[str, Any], method: str = "Manual", group_id: Optional[str] = None) -> Optional[str]:
        """Create a card report in Notion."""
        try:
            logger.debug(f"Creating Notion report with data: {card_data}")
            logger.debug(f"Using database ID: {self.database_id}")
            
            # Get current date in ISO format
            current_date = datetime.now().isoformat()
            
            # Create the page
            new_page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"text": {"content": card_data["name"]}}]},
                    "Set": {"rich_text": [{"text": {"content": card_data["collection"]}}]},
                    "Rarity": {"rich_text": [{"text": {"content": card_data["rarity"]}}]},
                    "Market Price": {"number": card_data["market_price"]},
                    "Method": {"rich_text": [{"text": {"content": method}}]},
                    "Card Image": {"url": card_data["image_url"]},
                    "Group ID": {"rich_text": [{"text": {"content": group_id or ""}}]},
                    "Variant Number": {"rich_text": [{"text": {"content": card_data["variant_number"]}}]},
                    "Created Date": {"date": {"start": current_date}},
                    "Card ID": {"rich_text": [{"text": {"content": card_data["card_id"]}}]},
                    "Repeated": {"checkbox": card_data.get("repeated", False)}
                }
            )
            
            logger.info(f"Success! Card report created with page ID: {new_page['id']}")
            return new_page["id"]
            
        except Exception as e:
            logger.error(f"Error creating card report: {str(e)}")
            logger.error(f"Card data: {card_data}")
            logger.error(f"Database ID: {self.database_id}")
            logger.error(f"Exception type: {type(e)}")
            return None 