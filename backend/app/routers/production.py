from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.crud import materials as material_crud
from app.crud import production as crud

router = APIRouter(
    prefix="/production",
    tags=["production"]
)

# --- ISSUE MATERIAL TO PRODUCTION ---

@router.post("/inventory/", status_code=status.HTTP_200_OK)
def issue_material(
    payload: schemas.ProductionMaterialCreate,
    db: Session = Depends(get_db)
):
    # 1. Verify material exists in catalog
    material = material_crud.get_catalog_by_number(db, payload.material_number)
    if not material:
        raise HTTPException(
            status_code=404,
            detail="Material catalog entry not found"
        )

    # 2. Validate quantity
    if payload.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    # 3. Move material using lot-specific logic (validates lot existence + balance internally)
    production_material = crud.issue_material_to_production(
        db,
        material_number=payload.material_number,
        lot_number=payload.lot_number,
        quantity=payload.quantity
    )

    return {
        "message": "Material successfully moved to production",
        "material_number": production_material.material_number,
        "lot_number": production_material.lot_number,
        "current_production_balance": production_material.quantity
    }


# --- VIEW PRODUCTION INVENTORY ---

@router.get(
    "/inventory/",
    response_model=list[schemas.ProductionStockReport]
)
def view_production_inventory(
    db: Session = Depends(get_db)
):
    """
    Returns all materials currently available
    in the production line.
    """

    materials = crud.get_all_production_materials(db)

    return [
        {
            "material_number": item.material_number,
            "material_name": item.material.material_name,
            "lot_number": item.lot_number,
            "quantity": item.quantity,
            "unit": item.material.unit
        }
        for item in materials
    ]