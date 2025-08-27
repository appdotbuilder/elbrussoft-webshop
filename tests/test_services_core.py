import pytest
from decimal import Decimal
from app.database import reset_db
from app.services import ProductService, CustomerService, DataSeederService
from app.models import ProductCreate


@pytest.fixture()
def fresh_db():
    """Reset database before each test."""
    reset_db()
    yield
    reset_db()


class TestProductServiceCore:
    def test_create_and_retrieve_product(self, fresh_db):
        """Test creating and retrieving a product."""
        product_data = ProductCreate(
            name="Core Test Product",
            description="A product for core testing",
            price=Decimal("99.99"),
            stock_quantity=5,
            sku="CORE-001",
            category="Testing",
            is_active=True,
        )

        created_product = ProductService.create_product(product_data)

        assert created_product.id is not None
        assert created_product.name == "Core Test Product"
        assert created_product.price == Decimal("99.99")
        assert created_product.stock_quantity == 5
        assert created_product.is_active

        # Retrieve the product
        retrieved_product = ProductService.get_product_by_id(created_product.id)
        assert retrieved_product is not None
        assert retrieved_product.name == "Core Test Product"

    def test_get_active_products(self, fresh_db):
        """Test retrieving active products."""
        # Create active product
        ProductService.create_product(
            ProductCreate(name="Active Product", description="This is active", price=Decimal("50.00"), is_active=True)
        )

        # Create inactive product
        ProductService.create_product(
            ProductCreate(
                name="Inactive Product", description="This is inactive", price=Decimal("25.00"), is_active=False
            )
        )

        active_products = ProductService.get_all_active_products()
        assert len(active_products) == 1
        assert active_products[0].name == "Active Product"

    def test_get_products_by_category(self, fresh_db):
        """Test retrieving products by category."""
        ProductService.create_product(
            ProductCreate(
                name="Web Service",
                description="Web development",
                price=Decimal("100.00"),
                category="Web Development",
                is_active=True,
            )
        )

        ProductService.create_product(
            ProductCreate(
                name="Mobile Service",
                description="Mobile development",
                price=Decimal("200.00"),
                category="Mobile Development",
                is_active=True,
            )
        )

        web_products = ProductService.get_products_by_category("Web Development")
        mobile_products = ProductService.get_products_by_category("Mobile Development")

        assert len(web_products) == 1
        assert len(mobile_products) == 1
        assert web_products[0].name == "Web Service"
        assert mobile_products[0].name == "Mobile Service"


class TestCustomerServiceCore:
    def test_create_customer(self, fresh_db):
        """Test creating a new customer."""
        customer = CustomerService.get_or_create_customer(
            email="test@example.com", first_name="John", last_name="Doe", phone="123-456-7890"
        )

        assert customer.id is not None
        assert customer.email == "test@example.com"
        assert customer.first_name == "John"
        assert customer.last_name == "Doe"
        assert customer.phone == "123-456-7890"

    def test_get_existing_customer(self, fresh_db):
        """Test retrieving existing customer."""
        # Create customer first time
        customer1 = CustomerService.get_or_create_customer(
            email="existing@example.com", first_name="Jane", last_name="Smith"
        )

        # Get same customer again
        customer2 = CustomerService.get_or_create_customer(
            email="existing@example.com", first_name="Different Name", last_name="Different Last"
        )

        # Should return same customer
        assert customer1.id == customer2.id
        assert customer1.email == customer2.email


class TestDataSeederServiceCore:
    def test_seed_sample_products(self, fresh_db):
        """Test seeding sample products."""
        # Initially no products
        products_before = ProductService.get_all_active_products()
        assert len(products_before) == 0

        # Seed products
        DataSeederService.seed_sample_products()

        # Should have products now
        products_after = ProductService.get_all_active_products()
        assert len(products_after) > 0

        # Check specific categories exist
        web_dev_products = ProductService.get_products_by_category("Web Development")
        software_dev_products = ProductService.get_products_by_category("Software Development")

        assert len(web_dev_products) > 0
        assert len(software_dev_products) > 0

    def test_seed_skip_if_products_exist(self, fresh_db):
        """Test that seeding skips if products already exist."""
        # Create a product manually
        ProductService.create_product(
            ProductCreate(name="Existing Product", description="Already exists", price=Decimal("50.00"))
        )

        products_before = ProductService.get_all_active_products()
        count_before = len(products_before)

        # Try to seed (should skip)
        DataSeederService.seed_sample_products()

        products_after = ProductService.get_all_active_products()
        count_after = len(products_after)

        # Should not have added new products
        assert count_after == count_before


class TestProductServiceEdgeCases:
    def test_get_nonexistent_product(self, fresh_db):
        """Test retrieving non-existent product."""
        product = ProductService.get_product_by_id(99999)
        assert product is None

    def test_get_products_nonexistent_category(self, fresh_db):
        """Test getting products from non-existent category."""
        products = ProductService.get_products_by_category("Nonexistent Category")
        assert len(products) == 0

    def test_create_product_with_decimal_precision(self, fresh_db):
        """Test creating product with precise decimal values."""
        product_data = ProductCreate(
            name="Precision Test", description="Testing decimal precision", price=Decimal("123.45"), stock_quantity=0
        )

        product = ProductService.create_product(product_data)
        assert product.price == Decimal("123.45")
        assert product.stock_quantity == 0
