from nicegui import ui, app
from typing import List
import logging

from app.models import Product, PayPalPaymentRequest
from app.services import ProductService, PaymentService

logger = logging.getLogger(__name__)


def create():
    """Create the Elbrussoft web store application."""

    # Apply modern theme
    ui.colors(
        primary="#2563eb",  # Professional blue
        secondary="#64748b",  # Subtle gray
        accent="#10b981",  # Success green
        positive="#10b981",
        negative="#ef4444",  # Error red
        warning="#f59e0b",  # Warning amber
        info="#3b82f6",  # Info blue
    )

    # Add custom CSS for enhanced styling
    ui.add_head_html("""
    <style>
    .product-card {
        transition: all 0.3s ease;
        border-radius: 12px;
        overflow: hidden;
    }
    .product-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    .product-image {
        height: 200px;
        object-fit: cover;
        width: 100%;
    }
    .price-tag {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        font-weight: bold;
        padding: 8px 16px;
        border-radius: 20px;
        display: inline-block;
    }
    .buy-button {
        background: linear-gradient(45deg, #2563eb 0%, #1d4ed8 100%);
        transition: all 0.2s ease;
    }
    .buy-button:hover {
        background: linear-gradient(45deg, #1d4ed8 0%, #1e40af 100%);
        transform: scale(1.02);
    }
    .store-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    </style>
    """)

    @ui.page("/")
    def store_home():
        """Main store page displaying product catalog."""
        create_store_layout()

    @ui.page("/product/{product_id}")
    def product_detail(product_id: int):
        """Individual product detail page."""
        create_product_detail_page(product_id)

    @ui.page("/checkout/{product_id}")
    async def checkout_page(product_id: int):
        """Checkout page for a specific product."""
        await create_checkout_page(product_id)

    @ui.page("/payment/success")
    def payment_success():
        """Payment success page."""
        create_payment_success_page()

    @ui.page("/payment/cancelled")
    def payment_cancelled():
        """Payment cancelled page."""
        create_payment_cancelled_page()


def create_store_layout():
    """Create the main store layout with product catalog."""
    # Header
    with ui.element("header").classes("store-header p-8 text-center mb-8"):
        ui.label("Elbrussoft").classes("text-4xl font-bold mb-2")
        ui.label("Professional Software Development Services").classes("text-xl opacity-90")

    # Main content
    with ui.element("main").classes("container mx-auto px-4"):
        # Load and display products
        products = ProductService.get_all_active_products()

        if not products:
            create_empty_store_message()
        else:
            create_product_grid(products)

    # Footer
    with ui.element("footer").classes("mt-16 py-8 text-center text-gray-600 border-t"):
        ui.label("© 2025 Elbrussoft - Professional Software Development Services").classes("text-sm")


def create_empty_store_message():
    """Display message when no products are available."""
    with ui.card().classes("w-full max-w-2xl mx-auto p-8 text-center"):
        ui.icon("inventory_2", size="4rem").classes("text-gray-400 mb-4")
        ui.label("No products available at the moment").classes("text-xl text-gray-600 mb-4")
        ui.label("Please check back later for our latest software development services.").classes("text-gray-500")


def create_product_grid(products: List[Product]):
    """Create a responsive grid of product cards."""
    ui.label("Our Services").classes("text-3xl font-bold text-gray-800 mb-8 text-center")

    # Create responsive grid
    with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"):
        for product in products:
            create_product_card(product)


def create_product_card(product: Product):
    """Create an individual product card."""
    with ui.card().classes("product-card shadow-md hover:shadow-xl bg-white"):
        # Product image
        if product.image_url:
            ui.image(product.image_url).classes("product-image")
        else:
            # Fallback for products without images
            with ui.element("div").classes("product-image bg-gray-200 flex items-center justify-center"):
                ui.icon("code", size="3rem").classes("text-gray-400")

        # Product info
        with ui.card_section().classes("p-4"):
            # Category badge
            if product.category:
                ui.label(product.category).classes(
                    "text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full mb-2 inline-block"
                )

            # Product name
            ui.label(product.name).classes("text-lg font-bold text-gray-800 mb-2 line-clamp-2")

            # Description (truncated)
            description = product.description
            if len(description) > 120:
                description = description[:117] + "..."
            ui.label(description).classes("text-sm text-gray-600 mb-4 line-clamp-3")

            # Price and stock info
            with ui.row().classes("items-center justify-between mb-4"):
                ui.html(f'<span class="price-tag">${product.price}</span>')
                if product.stock_quantity > 0:
                    ui.label(f"{product.stock_quantity} in stock").classes("text-xs text-green-600")
                else:
                    ui.label("Out of stock").classes("text-xs text-red-600")

            # Action buttons
            product_id = product.id
            with ui.row().classes("gap-2 w-full"):
                ui.button("View Details", on_click=lambda pid=product_id: ui.navigate.to(f"/product/{pid}")).classes(
                    "flex-1"
                ).props("outline color=primary")

                if product.stock_quantity > 0:
                    ui.button("Buy Now", on_click=lambda pid=product_id: ui.navigate.to(f"/checkout/{pid}")).classes(
                        "buy-button text-white flex-1"
                    )
                else:
                    ui.button("Out of Stock").classes("flex-1 bg-gray-300 text-gray-500").props("disable")


def create_product_detail_page(product_id: int):
    """Create detailed product view page."""
    product = ProductService.get_product_by_id(product_id)

    if product is None:
        create_product_not_found_page()
        return

    if product.id is None:
        create_product_not_found_page()
        return

    # Header
    with ui.row().classes("items-center mb-6"):
        ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props("flat round")
        ui.label("Product Details").classes("text-2xl font-bold ml-4")

    # Product detail layout
    with ui.row().classes("gap-8 w-full"):
        # Left column - Image
        with ui.column().classes("w-full md:w-1/2"):
            if product.image_url:
                ui.image(product.image_url).classes("w-full rounded-lg shadow-md")
            else:
                with ui.card().classes("w-full h-96 flex items-center justify-center bg-gray-100"):
                    ui.icon("code", size="6rem").classes("text-gray-400")

        # Right column - Details
        with ui.column().classes("w-full md:w-1/2 space-y-4"):
            # Category
            if product.category:
                ui.label(product.category).classes(
                    "text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full inline-block"
                )

            # Title
            ui.label(product.name).classes("text-3xl font-bold text-gray-800")

            # Price
            ui.html(f'<div class="price-tag text-2xl">${product.price}</div>')

            # Stock status
            with ui.row().classes("items-center gap-2"):
                if product.stock_quantity > 0:
                    ui.icon("check_circle", color="green")
                    ui.label(f"{product.stock_quantity} in stock").classes("text-green-600 font-medium")
                else:
                    ui.icon("cancel", color="red")
                    ui.label("Out of stock").classes("text-red-600 font-medium")

            # Description
            ui.label("Description").classes("text-lg font-semibold text-gray-800 mt-6")
            ui.label(product.description).classes("text-gray-600 leading-relaxed")

            # SKU
            if product.sku:
                ui.label(f"SKU: {product.sku}").classes("text-sm text-gray-500 mt-4")

            # Buy button
            if product.stock_quantity > 0:
                ui.button(
                    "Buy Now - Proceed to Checkout",
                    on_click=lambda: ui.navigate.to(f"/checkout/{product.id}"),
                    icon="shopping_cart",
                ).classes("buy-button text-white text-lg px-8 py-3 mt-6 w-full")
            else:
                ui.button("Out of Stock").classes("bg-gray-300 text-gray-500 text-lg px-8 py-3 mt-6 w-full").props(
                    "disable"
                )


async def create_checkout_page(product_id: int):
    """Create checkout page for purchasing a product."""
    product = ProductService.get_product_by_id(product_id)

    if product is None:
        create_product_not_found_page()
        return

    if product.stock_quantity <= 0:
        create_out_of_stock_page(product)
        return

    # Header
    with ui.row().classes("items-center mb-6"):
        ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to(f"/product/{product.id}")).props("flat round")
        ui.label("Checkout").classes("text-2xl font-bold ml-4")

    # Checkout layout
    with ui.row().classes("gap-8 w-full max-w-6xl mx-auto"):
        # Left column - Order summary
        with ui.column().classes("w-full md:w-1/2"):
            with ui.card().classes("p-6"):
                ui.label("Order Summary").classes("text-xl font-bold mb-4")

                # Product summary
                with ui.row().classes("items-center gap-4 mb-4"):
                    if product.image_url:
                        ui.image(product.image_url).classes("w-20 h-20 object-cover rounded")
                    else:
                        with ui.element("div").classes(
                            "w-20 h-20 bg-gray-200 rounded flex items-center justify-center"
                        ):
                            ui.icon("code", size="2rem").classes("text-gray-400")

                    with ui.column().classes("flex-1"):
                        ui.label(product.name).classes("font-semibold")
                        if product.category:
                            ui.label(product.category).classes("text-sm text-gray-500")

                # Price breakdown
                ui.separator().classes("my-4")
                with ui.row().classes("justify-between"):
                    ui.label("Subtotal:")
                    ui.label(f"${product.price}").classes("font-semibold")
                with ui.row().classes("justify-between"):
                    ui.label("Tax:")
                    ui.label("$0.00").classes("text-gray-600")
                with ui.row().classes("justify-between"):
                    ui.label("Shipping:")
                    ui.label("FREE").classes("text-green-600")

                ui.separator().classes("my-4")
                with ui.row().classes("justify-between text-xl font-bold"):
                    ui.label("Total:")
                    ui.label(f"${product.price}")

        # Right column - Checkout form
        with ui.column().classes("w-full md:w-1/2"):
            await create_checkout_form(product)


async def create_checkout_form(product: Product):
    """Create the checkout form for customer information."""
    with ui.card().classes("p-6"):
        ui.label("Customer Information").classes("text-xl font-bold mb-4")

        # Customer form
        with ui.column().classes("space-y-4"):
            # Contact information
            ui.label("Contact Information").classes("text-lg font-semibold text-gray-700")
            customer_email = ui.input("Email Address", placeholder="your@email.com").classes("w-full")

            with ui.row().classes("gap-4 w-full"):
                customer_first_name = ui.input("First Name", placeholder="John").classes("flex-1")
                customer_last_name = ui.input("Last Name", placeholder="Doe").classes("flex-1")

            customer_phone = ui.input("Phone Number (Optional)", placeholder="+1 (555) 123-4567").classes("w-full")

            ui.separator().classes("my-6")

            # Shipping information
            ui.label("Shipping Information").classes("text-lg font-semibold text-gray-700")
            shipping_address1 = ui.input("Address Line 1", placeholder="123 Main Street").classes("w-full")
            shipping_address2 = ui.input("Address Line 2 (Optional)", placeholder="Apt, Suite, etc.").classes("w-full")

            with ui.row().classes("gap-4 w-full"):
                shipping_city = ui.input("City", placeholder="New York").classes("flex-1")
                shipping_state = ui.input("State/Province", placeholder="NY").classes("flex-1")

            with ui.row().classes("gap-4 w-full"):
                shipping_postal = ui.input("Postal Code", placeholder="10001").classes("flex-1")
                shipping_country = ui.input("Country", value="United States").classes("flex-1")

            ui.separator().classes("my-6")

            # Payment section
            ui.label("Payment Method").classes("text-lg font-semibold text-gray-700")
            with ui.row().classes("items-center gap-2 mb-4"):
                ui.icon("payment").classes("text-blue-600")
                ui.label("PayPal").classes("font-medium")
                ui.label("(Secure Payment Processing)").classes("text-sm text-gray-500")

            # Submit button
            async def process_payment():
                """Process the payment through PayPal."""
                # Validate required fields
                if not all(
                    [
                        customer_email.value,
                        customer_first_name.value,
                        customer_last_name.value,
                        shipping_address1.value,
                        shipping_city.value,
                        shipping_state.value,
                        shipping_postal.value,
                        shipping_country.value,
                    ]
                ):
                    ui.notify("Please fill in all required fields", type="negative")
                    return

                # Ensure product has valid ID
                if product.id is None:
                    ui.notify("Product ID is missing", type="negative")
                    return

                # Create payment request
                payment_request = PayPalPaymentRequest(
                    product_id=product.id,
                    customer_email=customer_email.value.strip(),
                    customer_first_name=customer_first_name.value.strip(),
                    customer_last_name=customer_last_name.value.strip(),
                    shipping_address_line1=shipping_address1.value.strip(),
                    shipping_address_line2=shipping_address2.value.strip() if shipping_address2.value else None,
                    shipping_city=shipping_city.value.strip(),
                    shipping_state=shipping_state.value.strip(),
                    shipping_postal_code=shipping_postal.value.strip(),
                    shipping_country=shipping_country.value.strip(),
                    phone=customer_phone.value.strip() if customer_phone.value else None,
                )

                # Create PayPal payment
                payment_response = PaymentService.create_paypal_payment(payment_request)

                if payment_response is None:
                    ui.notify("Failed to create payment. Please try again.", type="negative")
                    return

                # Store payment info in app storage for completion
                app.storage.user["pending_payment_id"] = payment_response.payment_id
                app.storage.user["pending_order_id"] = payment_response.order_id

                # Simulate PayPal redirect
                ui.notify("Redirecting to PayPal...", type="info")

                # For demo purposes, show PayPal simulation dialog
                await show_paypal_simulation(payment_response)

            ui.button(f"Pay ${product.price} with PayPal", on_click=process_payment, icon="payment").classes(
                "buy-button text-white w-full text-lg py-3 mt-6"
            )


async def show_paypal_simulation(payment_response):
    """Show PayPal payment simulation dialog."""
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("PayPal Payment Simulation").classes("text-xl font-bold mb-4")
        ui.label("This is a demonstration of PayPal integration.").classes("text-gray-600 mb-4")
        ui.label(f"Payment ID: {payment_response.payment_id}").classes("text-sm text-gray-500 mb-2")
        ui.label(f"Order ID: {payment_response.order_id}").classes("text-sm text-gray-500 mb-6")

        ui.label("Choose an action:").classes("font-medium mb-4")

        with ui.row().classes("gap-2 w-full"):
            ui.button(
                "Complete Payment", on_click=lambda: complete_demo_payment(dialog, payment_response.payment_id)
            ).classes("bg-green-500 text-white flex-1")

            ui.button(
                "Cancel Payment", on_click=lambda: cancel_demo_payment(dialog, payment_response.payment_id)
            ).classes("bg-red-500 text-white flex-1")

    await dialog


def complete_demo_payment(dialog, payment_id: str):
    """Complete the demo payment."""
    # Simulate successful PayPal completion
    payer_id = f"PAYER{payment_id[-8:]}"
    success = PaymentService.complete_paypal_payment(payment_id, payer_id)

    dialog.close()

    if success:
        ui.navigate.to("/payment/success")
    else:
        ui.notify("Payment completion failed", type="negative")


def cancel_demo_payment(dialog, payment_id: str):
    """Cancel the demo payment."""
    PaymentService.cancel_paypal_payment(payment_id)
    dialog.close()
    ui.navigate.to("/payment/cancelled")


def create_payment_success_page():
    """Create payment success confirmation page."""
    with ui.column().classes("items-center text-center max-w-2xl mx-auto mt-16"):
        ui.icon("check_circle", size="6rem").classes("text-green-500 mb-6")
        ui.label("Payment Successful!").classes("text-4xl font-bold text-green-600 mb-4")
        ui.label("Thank you for your purchase. Your order has been confirmed.").classes("text-xl text-gray-600 mb-6")

        # Order details
        payment_id = app.storage.user.get("pending_payment_id")
        order_id = app.storage.user.get("pending_order_id")

        if payment_id and order_id:
            with ui.card().classes("p-6 bg-green-50 border border-green-200 mb-6"):
                ui.label("Order Details").classes("text-lg font-bold mb-2")
                ui.label(f"Order ID: {order_id}").classes("text-sm text-gray-600")
                ui.label(f"Payment ID: {payment_id}").classes("text-sm text-gray-600")

        ui.label("You will receive a confirmation email shortly.").classes("text-gray-600 mb-8")

        with ui.row().classes("gap-4"):
            ui.button("Continue Shopping", on_click=lambda: ui.navigate.to("/"), icon="shopping_cart").classes(
                "bg-blue-500 text-white px-6 py-2"
            )


def create_payment_cancelled_page():
    """Create payment cancelled page."""
    with ui.column().classes("items-center text-center max-w-2xl mx-auto mt-16"):
        ui.icon("cancel", size="6rem").classes("text-orange-500 mb-6")
        ui.label("Payment Cancelled").classes("text-4xl font-bold text-orange-600 mb-4")
        ui.label("Your payment was cancelled. No charges have been made.").classes("text-xl text-gray-600 mb-8")

        with ui.row().classes("gap-4"):
            ui.button("Try Again", on_click=lambda: ui.navigate.back(), icon="refresh").classes(
                "bg-orange-500 text-white px-6 py-2"
            )

            ui.button("Continue Shopping", on_click=lambda: ui.navigate.to("/"), icon="shopping_cart").classes(
                "bg-blue-500 text-white px-6 py-2"
            )


def create_product_not_found_page():
    """Create product not found error page."""
    with ui.column().classes("items-center text-center max-w-2xl mx-auto mt-16"):
        ui.icon("error", size="6rem").classes("text-red-500 mb-6")
        ui.label("Product Not Found").classes("text-4xl font-bold text-red-600 mb-4")
        ui.label("The requested product could not be found.").classes("text-xl text-gray-600 mb-8")

        ui.button("Back to Store", on_click=lambda: ui.navigate.to("/"), icon="store").classes(
            "bg-blue-500 text-white px-6 py-2"
        )


def create_out_of_stock_page(product: Product):
    """Create out of stock page."""
    with ui.column().classes("items-center text-center max-w-2xl mx-auto mt-16"):
        ui.icon("inventory", size="6rem").classes("text-orange-500 mb-6")
        ui.label("Out of Stock").classes("text-4xl font-bold text-orange-600 mb-4")
        ui.label(f'"{product.name}" is currently out of stock.').classes("text-xl text-gray-600 mb-8")

        with ui.row().classes("gap-4"):
            ui.button(
                "View Product Details", on_click=lambda: ui.navigate.to(f"/product/{product.id}"), icon="info"
            ).classes("bg-blue-500 text-white px-6 py-2")

            ui.button("Continue Shopping", on_click=lambda: ui.navigate.to("/"), icon="shopping_cart").classes(
                "bg-blue-500 text-white px-6 py-2"
            )
