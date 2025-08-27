from nicegui import ui
from typing import Optional
from decimal import Decimal
import logging

from app.models import Product, ProductCreate
from app.services import ProductService

logger = logging.getLogger(__name__)


def create():
    """Create admin interface for managing products."""

    @ui.page("/admin")
    def admin_dashboard():
        """Admin dashboard for product management."""
        create_admin_layout()

    @ui.page("/admin/products/new")
    def new_product():
        """Create new product form."""
        create_new_product_form()

    @ui.page("/admin/products/edit/{product_id}")
    def edit_product(product_id: int):
        """Edit existing product form."""
        create_edit_product_form(product_id)


def create_admin_layout():
    """Create the main admin dashboard layout."""
    # Header
    with ui.element("header").classes("bg-gray-800 text-white p-4 mb-8"):
        with ui.row().classes("items-center justify-between"):
            ui.label("Elbrussoft Admin Dashboard").classes("text-2xl font-bold")
            ui.button("View Store", on_click=lambda: ui.navigate.to("/")).props("outline color=white")

    # Main content
    with ui.element("main").classes("container mx-auto px-4"):
        ui.label("Product Management").classes("text-3xl font-bold mb-6")

        # Action buttons
        with ui.row().classes("gap-4 mb-8"):
            ui.button("Add New Product", on_click=lambda: ui.navigate.to("/admin/products/new"), icon="add").classes(
                "bg-green-500 text-white px-4 py-2"
            )

            ui.button("Refresh Products", on_click=lambda: ui.navigate.reload(), icon="refresh").classes(
                "bg-blue-500 text-white px-4 py-2"
            )

        # Products table
        create_products_table()


def create_products_table():
    """Create a table displaying all products."""
    products = ProductService.get_all_active_products()

    if not products:
        with ui.card().classes("p-8 text-center"):
            ui.icon("inventory_2", size="4rem").classes("text-gray-400 mb-4")
            ui.label("No products found").classes("text-xl text-gray-600 mb-4")
            ui.button("Create First Product", on_click=lambda: ui.navigate.to("/admin/products/new")).classes(
                "bg-green-500 text-white px-4 py-2"
            )
        return

    # Table columns
    columns = [
        {"name": "id", "label": "ID", "field": "id", "sortable": True},
        {"name": "name", "label": "Name", "field": "name", "sortable": True},
        {"name": "category", "label": "Category", "field": "category", "sortable": True},
        {"name": "price", "label": "Price", "field": "price", "sortable": True},
        {"name": "stock", "label": "Stock", "field": "stock_quantity", "sortable": True},
        {"name": "active", "label": "Active", "field": "is_active"},
        {"name": "actions", "label": "Actions", "field": "actions"},
    ]

    # Convert products to table rows
    rows = []
    for product in products:
        rows.append(
            {
                "id": product.id,
                "name": product.name,
                "category": product.category or "N/A",
                "price": f"${product.price}",
                "stock_quantity": product.stock_quantity,
                "is_active": "✓" if product.is_active else "✗",
                "actions": product.id,  # Store ID for actions
            }
        )

    # Create table
    table = ui.table(columns=columns, rows=rows, pagination=10).classes("w-full")

    # Add action buttons to each row
    with table.add_slot("body-cell-actions"):
        ui.button("Edit", icon="edit").props("size=sm color=primary").classes("mr-2")
        ui.button("Delete", icon="delete").props("size=sm color=negative")

    # Handle edit button clicks
    def handle_edit(e):
        product_id = e.args["row"]["actions"]
        ui.navigate.to(f"/admin/products/edit/{product_id}")

    # Handle delete button clicks
    def handle_delete(e):
        product_id = e.args["row"]["actions"]
        delete_product_with_confirmation(product_id)

    table.on("editClick", handle_edit)
    table.on("deleteClick", handle_delete)


def create_new_product_form():
    """Create form for adding new products."""
    # Header
    with ui.row().classes("items-center mb-6"):
        ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin")).props("flat round")
        ui.label("Add New Product").classes("text-2xl font-bold ml-4")

    # Form
    with ui.card().classes("max-w-4xl mx-auto p-6"):
        create_product_form(None)


def create_edit_product_form(product_id: int):
    """Create form for editing existing products."""
    product = ProductService.get_product_by_id(product_id)

    if product is None:
        with ui.column().classes("items-center text-center max-w-2xl mx-auto mt-16"):
            ui.icon("error", size="4rem").classes("text-red-500 mb-4")
            ui.label("Product Not Found").classes("text-2xl font-bold text-red-600 mb-4")
            ui.button("Back to Admin", on_click=lambda: ui.navigate.to("/admin")).classes(
                "bg-blue-500 text-white px-4 py-2"
            )
        return

    # Header
    with ui.row().classes("items-center mb-6"):
        ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin")).props("flat round")
        ui.label(f"Edit Product: {product.name}").classes("text-2xl font-bold ml-4")

    # Form
    with ui.card().classes("max-w-4xl mx-auto p-6"):
        create_product_form(product)


def create_product_form(product: Optional[Product] = None):
    """Create product form (used for both new and edit)."""
    is_edit = product is not None

    with ui.column().classes("space-y-6"):
        # Basic Information
        ui.label("Basic Information").classes("text-xl font-bold")

        name_input = ui.input("Product Name", value=product.name if is_edit else "").classes("w-full")
        name_input.props("outlined")

        category_input = ui.input("Category", value=product.category or "" if is_edit else "").classes("w-full")
        category_input.props("outlined")

        description_input = (
            ui.textarea("Description", value=product.description if is_edit else "")
            .classes("w-full")
            .props("outlined rows=4")
        )

        # Pricing and Inventory
        ui.separator()
        ui.label("Pricing & Inventory").classes("text-xl font-bold")

        with ui.row().classes("gap-4 w-full"):
            price_input = ui.number(
                "Price ($)", value=float(product.price) if is_edit else None, min=0.01, step=0.01, precision=2
            ).classes("flex-1")
            price_input.props("outlined")

            stock_input = ui.number(
                "Stock Quantity", value=product.stock_quantity if is_edit else 0, min=0, step=1
            ).classes("flex-1")
            stock_input.props("outlined")

        sku_input = ui.input("SKU (Optional)", value=product.sku or "" if is_edit else "").classes("w-full")
        sku_input.props("outlined")

        # Additional Settings
        ui.separator()
        ui.label("Additional Settings").classes("text-xl font-bold")

        image_url_input = ui.input("Image URL (Optional)", value=product.image_url or "" if is_edit else "").classes(
            "w-full"
        )
        image_url_input.props("outlined")

        active_checkbox = ui.checkbox(
            "Product is active and visible in store", value=product.is_active if is_edit else True
        )

        # Action buttons
        ui.separator()

        def save_product():
            """Save the product (create new or update existing)."""
            # Validate required fields
            if not name_input.value or not description_input.value or price_input.value is None:
                ui.notify("Please fill in all required fields", type="negative")
                return

            try:
                if is_edit:
                    # Note: This is a simplified example - in a real app you'd implement update_product
                    ui.notify("Product update functionality would be implemented here", type="info")
                    ui.navigate.to("/admin")

                else:
                    # Create new product
                    product_data = ProductCreate(
                        name=name_input.value.strip(),
                        description=description_input.value.strip(),
                        price=Decimal(str(price_input.value)),
                        stock_quantity=int(stock_input.value) if stock_input.value is not None else 0,
                        sku=sku_input.value.strip() if sku_input.value else None,
                        category=category_input.value.strip() if category_input.value else None,
                        image_url=image_url_input.value.strip() if image_url_input.value else None,
                        is_active=active_checkbox.value,
                    )

                    new_product = ProductService.create_product(product_data)
                    ui.notify(f'Product "{new_product.name}" created successfully!', type="positive")
                    ui.navigate.to("/admin")

            except Exception as e:
                logger.error(f"Error saving product: {str(e)}")
                ui.notify(f"Error saving product: {str(e)}", type="negative")

        with ui.row().classes("gap-4 justify-end"):
            ui.button("Cancel", on_click=lambda: ui.navigate.to("/admin")).props("outline")

            ui.button("Update Product" if is_edit else "Create Product", on_click=save_product, icon="save").classes(
                "bg-green-500 text-white px-6 py-2"
            )


def delete_product_with_confirmation(product_id: int):
    """Show confirmation dialog for product deletion."""
    product = ProductService.get_product_by_id(product_id)
    if product is None:
        ui.notify("Product not found", type="negative")
        return

    # For demo purposes, just show a notification
    ui.notify(f"Would delete product: {product.name}", type="info")
