import asyncio
import logging
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from .scraper_service.services import (
    scrape_page,
)  # Ajusta la ruta según tu estructura

# Forzar SelectorEventLoop en Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title="Google Maps Scraper API")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Pydantic model for response
class ScrapeResponse(BaseModel):
    results: Optional[List[dict]]


@app.get("/scrape", response_model=ScrapeResponse)
async def scrape_maps(
    service: str,
    location: str,
    ads_limit: int = 5,
    social_links: Optional[str] = None,
    debug: bool = False,
):
    """
    Endpoint to scrape Google Maps data based on provided query parameters.

    Query Parameters:
    - service: The service to search for (e.g., "restaurant").
    - location: The location to search in (e.g., "New York").
    - ads_limit: Maximum number of ads to scrape (default: 5).
    - social_links: Comma-separated list of social media platforms to extract (e.g., "facebook,instagram").
    - debug: Enable debug logging if true (default: false).
    """
    try:
        # Set logging level based on debug parameter
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        else:
            logging.getLogger().setLevel(logging.INFO)

        # Convert comma-separated social_links string to list if provided
        social_links_list = social_links.split(",") if social_links else []

        logger.debug(
            f"Parameters: service={service}, location={location}, ads_limit={ads_limit}, social_links={social_links_list}"
        )

        # Call the scrape_page function
        results = await scrape_page(
            service=service,
            location=location,
            ads_limit=ads_limit,
            social_links=social_links_list,
        )

        if results is None:
            logger.error("Scraping returned no results")
            raise HTTPException(
                status_code=500, detail="Failed to scrape data from Google Maps"
            )

        logger.info(f"Successfully scraped {len(results)} ads")
        return {"results": results}

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during scraping: {str(e)}")


# Cerrar el navegador al apagar la aplicación
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Cerrando el navegador...")
    
    
