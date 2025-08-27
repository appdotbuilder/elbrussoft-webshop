from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum


# Enums for status tracking
class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrderStatus(str, Enum):
    CREATED = "created"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# Persistent models (stored in database)
class Product(SQLModel, table=True):
    __tablename__ = "products"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, index=True)
    description: str = Field(max_length=2000)
    price: Decimal = Field(decimal_places=2, max_digits=10, ge=0)
    is_active: bool = Field(default=True, index=True)
    stock_quantity: int = Field(default=0, ge=0)
    sku: Optional[str] = Field(default=None, max_length=100, unique=True, index=True)
    category: Optional[str] = Field(default=None, max_length=100, index=True)
    image_url: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    order_items: List["OrderItem"] = Relationship(back_populates="product")


class Customer(SQLModel, table=True):
    __tablename__ = "customers"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, max_length=255, index=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    orders: List["Order"] = Relationship(back_populates="customer")


class Order(SQLModel, table=True):
    __tablename__ = "orders"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_number: str = Field(unique=True, max_length=50, index=True)
    customer_id: int = Field(foreign_key="customers.id", index=True)
    status: OrderStatus = Field(default=OrderStatus.CREATED, index=True)
    total_amount: Decimal = Field(decimal_places=2, max_digits=10, ge=0)
    currency: str = Field(default="USD", max_length=3)

    # Shipping information
    shipping_first_name: str = Field(max_length=100)
    shipping_last_name: str = Field(max_length=100)
    shipping_address_line1: str = Field(max_length=255)
    shipping_address_line2: Optional[str] = Field(default=None, max_length=255)
    shipping_city: str = Field(max_length=100)
    shipping_state: str = Field(max_length=100)
    shipping_postal_code: str = Field(max_length=20)
    shipping_country: str = Field(max_length=100)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    customer: Customer = Relationship(back_populates="orders")
    order_items: List["OrderItem"] = Relationship(back_populates="order")
    payments: List["Payment"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(decimal_places=2, max_digits=10, ge=0)
    total_price: Decimal = Field(decimal_places=2, max_digits=10, ge=0)

    # Relationships
    order: Order = Relationship(back_populates="order_items")
    product: Product = Relationship(back_populates="order_items")


class Payment(SQLModel, table=True):
    __tablename__ = "payments"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    payment_method: str = Field(default="paypal", max_length=50)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, index=True)
    amount: Decimal = Field(decimal_places=2, max_digits=10, ge=0)
    currency: str = Field(default="USD", max_length=3)

    # PayPal specific fields
    paypal_payment_id: Optional[str] = Field(default=None, max_length=100, index=True)
    paypal_payer_id: Optional[str] = Field(default=None, max_length=100)
    paypal_payment_token: Optional[str] = Field(default=None, max_length=100)

    # Transaction details
    transaction_id: Optional[str] = Field(default=None, max_length=100, unique=True, index=True)
    payment_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    order: Order = Relationship(back_populates="payments")


# Non-persistent schemas (for validation, forms, API requests/responses)
class ProductCreate(SQLModel, table=False):
    name: str = Field(max_length=200)
    description: str = Field(max_length=2000)
    price: Decimal = Field(decimal_places=2, max_digits=10, ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    sku: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)


class ProductUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Optional[Decimal] = Field(default=None, decimal_places=2, max_digits=10, ge=0)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    sku: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)
    image_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


class CustomerCreate(SQLModel, table=False):
    email: str = Field(max_length=255)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)


class OrderCreate(SQLModel, table=False):
    customer_id: int
    shipping_first_name: str = Field(max_length=100)
    shipping_last_name: str = Field(max_length=100)
    shipping_address_line1: str = Field(max_length=255)
    shipping_address_line2: Optional[str] = Field(default=None, max_length=255)
    shipping_city: str = Field(max_length=100)
    shipping_state: str = Field(max_length=100)
    shipping_postal_code: str = Field(max_length=20)
    shipping_country: str = Field(max_length=100)
    currency: str = Field(default="USD", max_length=3)


class OrderItemCreate(SQLModel, table=False):
    product_id: int
    quantity: int = Field(ge=1)


class PaymentCreate(SQLModel, table=False):
    order_id: int
    payment_method: str = Field(default="paypal", max_length=50)
    amount: Decimal = Field(decimal_places=2, max_digits=10, ge=0)
    currency: str = Field(default="USD", max_length=3)


class PayPalPaymentRequest(SQLModel, table=False):
    product_id: int
    customer_email: str = Field(max_length=255)
    customer_first_name: str = Field(max_length=100)
    customer_last_name: str = Field(max_length=100)
    shipping_address_line1: str = Field(max_length=255)
    shipping_address_line2: Optional[str] = Field(default=None, max_length=255)
    shipping_city: str = Field(max_length=100)
    shipping_state: str = Field(max_length=100)
    shipping_postal_code: str = Field(max_length=20)
    shipping_country: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)


class PayPalPaymentResponse(SQLModel, table=False):
    payment_id: str
    payment_url: str
    order_id: int
    status: PaymentStatus


# Product catalog response schemas
class ProductListResponse(SQLModel, table=False):
    id: int
    name: str
    description: str
    price: Decimal
    image_url: Optional[str]
    category: Optional[str]
    is_active: bool
    stock_quantity: int


class ProductDetailResponse(SQLModel, table=False):
    id: int
    name: str
    description: str
    price: Decimal
    image_url: Optional[str]
    category: Optional[str]
    is_active: bool
    stock_quantity: int
    sku: Optional[str]
    created_at: str
    updated_at: str
