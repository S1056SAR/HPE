import uvicorn
from api import app
from update_checker import UpdateChecker
import logging
from ingestion import DataIngestionPipeline
from vector_store import VectorStore
import os
from environment import GROQ_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY is not set. LLM functionality may be limited.")

def get_user_confirmation(message):
    """Get user confirmation for an action"""
    response = input(f"{message} (y/n): ").lower().strip()
    return response == 'y' or response == 'yes'

if __name__ == "__main__":
    try:
        update_checker = UpdateChecker()
        ingestion_pipeline = DataIngestionPipeline()
        vector_store = VectorStore()
        
        if get_user_confirmation("Do you want to reset the database?"):
            vector_store.reset_database()
            ingestion_pipeline.reset_ingestion_tracking()
        
        if os.path.exists("scraped_data.json"):
            if get_user_confirmation("Do you want to ingest data from scraped_data.json?"):
                ingestion_pipeline.ingest_scraped_data("scraped_data.json")
        
        if get_user_confirmation("Do you want to start web scraping for Aruba documentation?"):
            aruba_url = "https://arubanetworking.hpe.com/techdocs/AOS-CX/Consolidated_RNs/HTML-9300/Content/PDFs.htm"
            ingestion_pipeline.ingest_aruba_documentation(aruba_url)
        
        update_checker.start()
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        logger.info("Shutting down the application...")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
    finally:
        update_checker.stop()
