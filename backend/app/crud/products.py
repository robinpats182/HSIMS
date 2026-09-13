from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import (
    ProductDefinition, 
    ProductRecipe, 
    ProductLog, 
    ProductionMaterial, 
    MaterialDefinition
)
import app.schemas as schemas


# --- Product Master Catalog CRUD ---

def get_product_by_code(db: Session, product_code: str):
    """Fetches a product profile by product code."""
    return db.query(ProductDefinition).filter(
        ProductDefinition.product_code == product_code
    ).first()


def create_product_definition(db: Session, product: schemas.ProductCreate):
    """Creates a new product definition in the master catalog."""
    db_product = ProductDefinition(
        product_code=product.product_code,
        product_name=product.product_name,
        part_number=product.part_number,
        customers=product.customers
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# --- Recipe CRUD ---

def get_product_recipe(db: Session, product_code: str):
    """Fetches all recipe ingredient rules for a given product."""
    return db.query(ProductRecipe).filter(
        ProductRecipe.product_code == product_code
    ).all()


def save_product_recipe(db: Session, payload: schemas.CreateRecipeRequest):
    """Clears existing recipe entries for a product and inserts the new recipe components."""
    # Delete old recipe definitions
    db.query(ProductRecipe).filter(
        ProductRecipe.product_code == payload.product_code
    ).delete()

    # Save new recipe items
    for item in payload.ingredients:
        recipe_item = ProductRecipe(
            product_code=payload.product_code,
            material_number=item.material_number,
            required_quantity=item.required_quantity
        )
        db.add(recipe_item)

    db.commit()


# --- Production Inventory & FIFO Logic ---

def get_total_production_material_quantity(db: Session, material_number: str) -> float:
    """Calculates total stock available across all lots on the production line for a material."""
    return db.query(
        func.sum(ProductionMaterial.quantity)
    ).filter(
        ProductionMaterial.material_number == material_number,
        ProductionMaterial.quantity > 0
    ).scalar() or 0.0


def deduct_production_materials_fifo(db: Session, material_number: str, required_quantity: float):
    """
    Deducts material from the production line using FIFO.
    Orders active lots by lot_number ASC so the smallest/earliest lot is consumed first.
    """
    remaining_to_deduct = required_quantity

    active_lots = db.query(ProductionMaterial).filter(
        ProductionMaterial.material_number == material_number,
        ProductionMaterial.quantity > 0
    ).order_by(
        ProductionMaterial.lot_number.asc()  # Consumes smallest lot number first
    ).all()

    for lot in active_lots:
        if remaining_to_deduct <= 0:
            break

        take_qty = min(lot.quantity, remaining_to_deduct)
        lot.quantity -= take_qty
        remaining_to_deduct -= take_qty


# --- Product Logging & Ledger CRUD ---

def create_product_log(db: Session, log_data: schemas.ProductLogCreate) -> ProductLog:
    """Creates a new entry in the product transaction ledger."""
    new_log = ProductLog(
        product_code=log_data.product_code,
        date=log_data.date,
        quantity=log_data.quantity
    )
    db.add(new_log)
    return new_log


def get_all_product_logs(db: Session):
    """Fetches all logged product transactions."""
    return db.query(ProductLog).all()