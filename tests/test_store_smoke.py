import pytest
from decimal import Decimal

from app.database import reset_db
from app.services import ProductService, DataSeederService
from app.models import ProductCreate


@pytest.fixture()
def fresh_db():
    """Reset database before each test."""
    reset_db()
    yield
    reset_db()


def test_store_modules_import():
    """Test that store modules import without error."""
    import app.store
    import app.admin

    assert app.store is not None
    assert app.admin is not None


def test_store_with_sample_data(fresh_db):
    """Test that store works with sample data."""
    # Seed sample data
    DataSeederService.seed_sample_products()

    # Verify products were created
    products = ProductService.get_all_active_products()
    assert len(products) > 0

    # Verify specific products exist
    web_dev_products = ProductService.get_products_by_category("Web Development")
    assert len(web_dev_products) > 0

    found_main_product = False
    for product in products:
        if "Professional Web Development Package" in product.name:
            found_main_product = True
            break

    assert found_main_product


def test_store_with_custom_product(fresh_db):
    """Test store functionality with a custom product."""
    # Create test product
    product = ProductService.create_product(
        ProductCreate(
            name="Test Store Product",
            description="A test product for the store",
            price=Decimal("199.99"),
            stock_quantity=10,
            category="Testing",
            is_active=True,
        )
    )

    assert product.id is not None
    assert product.name == "Test Store Product"
    assert product.price == Decimal("199.99")

    # Verify it appears in active products
    active_products = ProductService.get_all_active_products()
    assert len(active_products) == 1
    assert active_products[0].name == "Test Store Product"
