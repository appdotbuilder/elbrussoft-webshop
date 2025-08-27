from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import uuid
import logging
from sqlmodel import select

from app.database import get_session
from app.models import (
    Product,
    Customer,
    Order,
    OrderItem,
    Payment,
    OrderStatus,
    PaymentStatus,
    ProductCreate,
    CustomerCreate,
    PayPalPaymentRequest,
    PayPalPaymentResponse,
)

logger = logging.getLogger(__name__)


class ProductService:
    @staticmethod
    def get_all_active_products() -> List[Product]:
        """Get all active products from the catalog."""
        with get_session() as session:
            statement = select(Product).where(Product.is_active == True)  # noqa: E712
            return list(session.exec(statement).all())

    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """Get a specific product by ID."""
        with get_session() as session:
            return session.get(Product, product_id)

    @staticmethod
    def create_product(product_data: ProductCreate) -> Product:
        """Create a new product."""
        with get_session() as session:
            product = Product(**product_data.model_dump())
            product.created_at = datetime.utcnow()
            product.updated_at = datetime.utcnow()
            session.add(product)
            session.commit()
            session.refresh(product)
            return product

    @staticmethod
    def get_products_by_category(category: str) -> List[Product]:
        """Get all active products in a specific category."""
        with get_session() as session:
            statement = select(Product).where(
                Product.is_active == True,  # noqa: E712
                Product.category == category,
            )
            return list(session.exec(statement).all())


class CustomerService:
    @staticmethod
    def get_or_create_customer(email: str, first_name: str, last_name: str, phone: Optional[str] = None) -> Customer:
        """Get existing customer by email or create new one."""
        with get_session() as session:
            # Try to find existing customer
            statement = select(Customer).where(Customer.email == email)
            existing_customer = session.exec(statement).first()

            if existing_customer:
                return existing_customer

            # Create new customer
            customer_data = CustomerCreate(email=email, first_name=first_name, last_name=last_name, phone=phone)
            customer = Customer(**customer_data.model_dump())
            customer.created_at = datetime.utcnow()
            customer.updated_at = datetime.utcnow()
            session.add(customer)
            session.commit()
            session.refresh(customer)
            return customer


class OrderService:
    @staticmethod
    def create_order(customer: Customer, product: Product, shipping_data: dict) -> Order:
        """Create a new order for a single product."""
        with get_session() as session:
            # Generate unique order number
            order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

            # Ensure customer has ID
            if customer.id is None:
                raise ValueError("Customer must have an ID")

            # Create order
            order = Order(
                order_number=order_number,
                customer_id=customer.id,
                status=OrderStatus.CREATED,
                total_amount=product.price,
                currency="USD",
                shipping_first_name=shipping_data["shipping_first_name"],
                shipping_last_name=shipping_data["shipping_last_name"],
                shipping_address_line1=shipping_data["shipping_address_line1"],
                shipping_address_line2=shipping_data.get("shipping_address_line2"),
                shipping_city=shipping_data["shipping_city"],
                shipping_state=shipping_data["shipping_state"],
                shipping_postal_code=shipping_data["shipping_postal_code"],
                shipping_country=shipping_data["shipping_country"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(order)
            session.commit()
            session.refresh(order)

            # Ensure order and product have IDs
            if order.id is None:
                raise ValueError("Order must have an ID after creation")
            if product.id is None:
                raise ValueError("Product must have an ID")

            # Create order item
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=1,
                unit_price=product.price,
                total_price=product.price,
            )
            session.add(order_item)
            session.commit()

            return order

    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Order]:
        """Get order by ID."""
        with get_session() as session:
            return session.get(Order, order_id)

    @staticmethod
    def update_order_status(order_id: int, status: OrderStatus) -> Optional[Order]:
        """Update order status."""
        with get_session() as session:
            order = session.get(Order, order_id)
            if order is None:
                return None

            order.status = status
            order.updated_at = datetime.utcnow()
            session.add(order)
            session.commit()
            session.refresh(order)
            return order


class PaymentService:
    @staticmethod
    def create_paypal_payment(request: PayPalPaymentRequest) -> Optional[PayPalPaymentResponse]:
        """
        Create a PayPal payment for a product.
        This is a simplified demonstration - in production, this would integrate with PayPal API.
        """
        try:
            # Get product
            product = ProductService.get_product_by_id(request.product_id)
            if product is None:
                logger.error(f"Product not found: {request.product_id}")
                return None

            if not product.is_active:
                logger.error(f"Product not active: {request.product_id}")
                return None

            if product.stock_quantity <= 0:
                logger.error(f"Product out of stock: {request.product_id}")
                return None

            # Get or create customer
            customer = CustomerService.get_or_create_customer(
                email=request.customer_email,
                first_name=request.customer_first_name,
                last_name=request.customer_last_name,
                phone=request.phone,
            )

            # Create order
            shipping_data = {
                "shipping_first_name": request.customer_first_name,
                "shipping_last_name": request.customer_last_name,
                "shipping_address_line1": request.shipping_address_line1,
                "shipping_address_line2": request.shipping_address_line2,
                "shipping_city": request.shipping_city,
                "shipping_state": request.shipping_state,
                "shipping_postal_code": request.shipping_postal_code,
                "shipping_country": request.shipping_country,
            }

            order = OrderService.create_order(customer, product, shipping_data)

            # Create payment record
            with get_session() as session:
                # Simulate PayPal payment ID and redirect URL
                payment_id = f"PAY-{str(uuid.uuid4()).replace('-', '').upper()[:20]}"
                payment_url = f"https://sandbox.paypal.com/checkoutnow?token={payment_id}"

                # Ensure order has ID
                if order.id is None:
                    raise ValueError("Order must have an ID")

                payment = Payment(
                    order_id=order.id,
                    payment_method="paypal",
                    status=PaymentStatus.PENDING,
                    amount=product.price,
                    currency="USD",
                    paypal_payment_id=payment_id,
                    paypal_payment_token=payment_id,
                    payment_data={
                        "product_name": product.name,
                        "customer_email": request.customer_email,
                        "created_via": "web_store",
                    },
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(payment)
                session.commit()
                session.refresh(payment)

                # Update order status
                OrderService.update_order_status(order.id, OrderStatus.PAYMENT_PENDING)

                return PayPalPaymentResponse(
                    payment_id=payment_id, payment_url=payment_url, order_id=order.id, status=PaymentStatus.PENDING
                )

        except Exception as e:
            logger.error(f"Error creating PayPal payment: {str(e)}")
            return None

    @staticmethod
    def complete_paypal_payment(payment_id: str, payer_id: str) -> bool:
        """
        Complete PayPal payment - simplified demonstration.
        In production, this would verify with PayPal API.
        """
        try:
            with get_session() as session:
                statement = select(Payment).where(Payment.paypal_payment_id == payment_id)
                payment = session.exec(statement).first()

                if payment is None:
                    logger.error(f"Payment not found: {payment_id}")
                    return False

                # Simulate successful payment completion
                payment.status = PaymentStatus.COMPLETED
                payment.paypal_payer_id = payer_id
                payment.completed_at = datetime.utcnow()
                payment.updated_at = datetime.utcnow()
                payment.transaction_id = f"TXN-{str(uuid.uuid4()).replace('-', '').upper()[:16]}"

                session.add(payment)
                session.commit()

                # Update order status
                if payment.order_id is not None:
                    OrderService.update_order_status(payment.order_id, OrderStatus.PAID)

                logger.info(f"Payment completed successfully: {payment_id}")
                return True

        except Exception as e:
            logger.error(f"Error completing PayPal payment: {str(e)}")
            return False

    @staticmethod
    def cancel_paypal_payment(payment_id: str) -> bool:
        """Cancel PayPal payment."""
        try:
            with get_session() as session:
                statement = select(Payment).where(Payment.paypal_payment_id == payment_id)
                payment = session.exec(statement).first()

                if payment is None:
                    logger.error(f"Payment not found: {payment_id}")
                    return False

                payment.status = PaymentStatus.CANCELLED
                payment.updated_at = datetime.utcnow()
                session.add(payment)
                session.commit()

                # Update order status
                if payment.order_id is not None:
                    OrderService.update_order_status(payment.order_id, OrderStatus.CANCELLED)

                logger.info(f"Payment cancelled: {payment_id}")
                return True

        except Exception as e:
            logger.error(f"Error cancelling PayPal payment: {str(e)}")
            return False

    @staticmethod
    def get_payment_by_id(payment_id: str) -> Optional[Payment]:
        """Get payment by PayPal payment ID."""
        with get_session() as session:
            statement = select(Payment).where(Payment.paypal_payment_id == payment_id)
            return session.exec(statement).first()


class DataSeederService:
    @staticmethod
    def seed_sample_products() -> None:
        """Seed database with sample products for demonstration."""
        sample_products = [
            ProductCreate(
                name="Professional Web Development Package",
                description="Complete web development solution including responsive design, modern framework integration, and deployment setup. Perfect for small to medium businesses looking to establish their online presence.",
                price=Decimal("1299.99"),
                stock_quantity=50,
                sku="WEB-DEV-PRO",
                category="Web Development",
                image_url="https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=400&h=300&fit=crop",
                is_active=True,
            ),
            ProductCreate(
                name="Custom Software Development",
                description="Tailored software solutions built to your specifications. Includes requirements analysis, development, testing, and documentation. Suitable for automation and business process optimization.",
                price=Decimal("2499.99"),
                stock_quantity=25,
                sku="SOFT-DEV-CUSTOM",
                category="Software Development",
                image_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=400&h=300&fit=crop",
                is_active=True,
            ),
            ProductCreate(
                name="Database Design & Optimization",
                description="Professional database architecture and optimization services. Includes schema design, performance tuning, and migration assistance for PostgreSQL, MySQL, and MongoDB.",
                price=Decimal("899.99"),
                stock_quantity=30,
                sku="DB-DESIGN-OPT",
                category="Database Services",
                image_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&h=300&fit=crop",
                is_active=True,
            ),
            ProductCreate(
                name="Mobile App Development (iOS/Android)",
                description="Cross-platform mobile application development using modern frameworks. Includes UI/UX design, development, testing, and app store deployment assistance.",
                price=Decimal("3199.99"),
                stock_quantity=15,
                sku="MOBILE-DEV-CROSS",
                category="Mobile Development",
                image_url="https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=400&h=300&fit=crop",
                is_active=True,
            ),
            ProductCreate(
                name="Cloud Infrastructure Setup",
                description="Complete cloud infrastructure design and implementation. Includes server setup, security configuration, monitoring, and backup solutions on AWS, Azure, or Google Cloud.",
                price=Decimal("1799.99"),
                stock_quantity=20,
                sku="CLOUD-INFRA-SETUP",
                category="Cloud Services",
                image_url="https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&h=300&fit=crop",
                is_active=True,
            ),
            ProductCreate(
                name="API Development & Integration",
                description="RESTful API development and third-party service integration. Includes authentication, documentation, testing, and deployment. Perfect for connecting systems and enabling automation.",
                price=Decimal("1599.99"),
                stock_quantity=35,
                sku="API-DEV-INTEG",
                category="Web Development",
                image_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&h=300&fit=crop",
                is_active=True,
            ),
            ProductCreate(
                name="E-commerce Solution",
                description="Complete e-commerce platform development with payment processing, inventory management, and admin dashboard. Includes responsive design and mobile optimization.",
                price=Decimal("2899.99"),
                stock_quantity=12,
                sku="ECOM-SOLUTION",
                category="Web Development",
                image_url="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=400&h=300&fit=crop",
                is_active=True,
            ),
            ProductCreate(
                name="DevOps Automation Package",
                description="CI/CD pipeline setup, automated testing, deployment automation, and monitoring configuration. Includes Docker containerization and Kubernetes orchestration setup.",
                price=Decimal("2199.99"),
                stock_quantity=18,
                sku="DEVOPS-AUTO-PKG",
                category="DevOps",
                image_url="https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=400&h=300&fit=crop",
                is_active=True,
            ),
        ]

        # Check if products already exist to avoid duplicates
        existing_products = ProductService.get_all_active_products()
        if len(existing_products) > 0:
            logger.info("Sample products already exist, skipping seed operation.")
            return

        # Create sample products
        created_count = 0
        for product_data in sample_products:
            try:
                ProductService.create_product(product_data)
                created_count += 1
            except Exception as e:
                logger.error(f"Error creating product {product_data.name}: {str(e)}")

        logger.info(f"Created {created_count} sample products.")
