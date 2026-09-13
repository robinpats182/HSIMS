from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import func
from app.models import MaterialLot, ProductionMaterial

# --- PRODUCTION INVENTORY CRUD ---

def get_production_material(
    db: Session,
    material_number: str,
    lot_number: str
):
    return db.query(ProductionMaterial).filter(
        ProductionMaterial.material_number == material_number,
        ProductionMaterial.lot_number == lot_number
    ).first()


def get_all_production_materials(db: Session):
    """Fetches all materials currently available in production."""
    return db.query(ProductionMaterial).all()

def get_warehouse_available_quantity(
    db: Session,
    material_number: str
):
    """Calculates total available warehouse quantity across all lots for a material."""
    return db.query(
        func.sum(MaterialLot.quantity)
    ).filter(
        MaterialLot.material_number == material_number
    ).scalar() or 0.0

def get_warehouse_lot_quantity(
    db: Session,
    material_number: str,
    lot_number: str
):
    """Fetches available quantity for a SPECIFIC material + lot number combination."""
    lot = db.query(MaterialLot).filter(
        MaterialLot.material_number == material_number,
        MaterialLot.lotno == lot_number
    ).first()
    
    return lot.quantity if lot else 0.0


def deduct_specific_lot_from_warehouse(
    db: Session,
    material_number: str,
    lot_number: str,
    quantity: float
):
    """
    Validates and deducts stock from a specific targeted lot number.
    Raises an error if the lot does not exist or has insufficient stock.
    """
    # 1. Fetch the exact lot
    lot = db.query(MaterialLot).filter(
        MaterialLot.material_number == material_number,
        MaterialLot.lotno == lot_number
    ).first()

    # 2. Validation: Check if lot exists
    if not lot:
        raise HTTPException(
            status_code=404,
            detail=f"Lot '{lot_number}' for material '{material_number}' does not exist in warehouse inventory."
        )

    # 3. Validation: Check if lot has enough quantity
    if lot.quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient quantity in Lot '{lot_number}'. "
                f"Requested: {quantity}, Available: {lot.quantity}"
            )
        )

    # 4. Deduct quantity
    lot.quantity -= quantity
    return lot.lotno, quantity


def add_to_production_inventory(
    db: Session,
    material_number: str,
    lot_number: str,
    quantity: float
):
    """Adds material into production inventory."""
    production_material = get_production_material(
        db,
        material_number,
        lot_number
    )

    if production_material:
        production_material.quantity += quantity
    else:
        production_material = ProductionMaterial(
            lot_number=lot_number,
            material_number=material_number,
            quantity=quantity
        )
        db.add(production_material)

    return production_material


def issue_material_to_production(
    db: Session,
    material_number: str,
    lot_number: str,
    quantity: float
):
    """
    Moves a specific lot's material from warehouse inventory to production inventory.
    """
    # 1. Validate & Deduct from targeted warehouse lot
    deducted_lotno, qty = deduct_specific_lot_from_warehouse(
        db,
        material_number,
        lot_number,
        quantity
    )

    # 2. Add to production inventory for that exact lot
    production_material = add_to_production_inventory(
        db,
        material_number,
        deducted_lotno,
        qty
    )

    # 3. Atomic commit
    db.commit()
    db.refresh(production_material)

    return production_material


def consume_production_material(
    db: Session,
    material_number: str,
    lot_number: str,
    quantity: float
):
    """
    Deducts material from production inventory for a specific lot.
    """
    production_material = get_production_material(
        db,
        material_number,
        lot_number
    )

    if not production_material:
        raise HTTPException(
            status_code=404,
            detail=f"Lot '{lot_number}' of material '{material_number}' not found on production line."
        )

    if production_material.quantity < quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient line inventory for Lot '{lot_number}'. "
                f"Requested: {quantity}, Available: {production_material.quantity}"
            )
        )

    production_material.quantity -= quantity
    db.commit()
    db.refresh(production_material)

    return production_material