from app.database import create_tables
from app.services import DataSeederService
import app.store
import app.admin
import logging

logger = logging.getLogger(__name__)


def startup() -> None:
    # this function is called before the first request
    create_tables()

    # Seed sample products for demonstration
    try:
        DataSeederService.seed_sample_products()
        logger.info("Sample products seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding sample products: {str(e)}")

    # Create store application
    app.store.create()

    # Create admin interface
    app.admin.create()
