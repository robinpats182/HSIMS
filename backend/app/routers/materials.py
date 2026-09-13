from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.crud import materials as crud 

router = APIRouter(prefix="/materials", tags=["materials"])

# --- CATALOG ENDPOINTS ---
@router.post("/catalog/", response_model=schemas.CatalogResponse, status_code=status.HTTP_201_CREATED)
def register_material(item: schemas.CatalogCreate, db: Session = Depends(get_db)):
    db_item = crud.get_catalog_by_number(db, item.material_number)
    if db_item:
        raise HTTPException(status_code=400, detail="Material ID code already exists")
    return crud.create_catalog_item(db, item)

@router.get("/catalog/", response_model=list[schemas.CatalogResponse])
def view_all_catalog_items(db: Session = Depends(get_db)):
    """Returns a list of all registered master materials in the system."""
    return crud.get_all_catalog_items(db)

@router.put("/catalog/by-number/{material_number}", response_model=schemas.CatalogResponse)
def update_by_number(material_number: str, updates: schemas.CatalogUpdate, db: Session = Depends(get_db)):
    db_item = crud.get_catalog_by_number(db, material_number)
    if not db_item:
        raise HTTPException(status_code=404, detail="Material not found")
    return crud.update_catalog_item(db, db_item, updates)

@router.delete("/catalog/by-number/{material_number}", status_code=status.HTTP_204_NO_CONTENT)
def delete_by_number(material_number: str, db: Session = Depends(get_db)):
    db_item = crud.get_catalog_by_number(db, material_number)
    if not db_item:
        raise HTTPException(status_code=404, detail="Material not found")
    crud.delete_catalog_item(db, db_item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- INVENTORY ENDPOINTS ---
@router.post("/inventory/", status_code=status.HTTP_200_OK)
def receive_stock(lot_data: schemas.LotCreate, db: Session = Depends(get_db)):
    # Verify catalog definition exists first
    if not crud.get_catalog_by_number(db, lot_data.material_number):
        raise HTTPException(status_code=404, detail="Material catalog entry not found")
    result = crud.receive_inventory_lot(db, lot_data)
    return {"message": "Inventory tracking updated", "id": result.id, "quantity": result.quantity}

@router.put("/inventory/{material_number}/{lotno}")
def correct_lot_balance(material_number: str, lotno: str, payload: schemas.LotUpdate, db: Session = Depends(get_db)):
    db_lot = crud.get_lot(db, material_number, lotno)
    if not db_lot:
        raise HTTPException(status_code=404, detail="Specific batch lot not found")
    return crud.set_lot_balance(db, db_lot, payload.quantity)

@router.delete("/inventory/{material_number}/{lotno}", status_code=status.HTTP_204_NO_CONTENT)
def remove_lot(material_number: str, lotno: str, db: Session = Depends(get_db)):
    db_lot = crud.get_lot(db, material_number, lotno)
    if not db_lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    crud.delete_lot_record(db, db_lot)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/inventory/", response_model=list[schemas.WarehouseStockReport])
def view_stock_sheet(db: Session = Depends(get_db)):
    lots = crud.get_all_warehouse_stock(db)
    # Mapping relational SQLAlchemy attributes cleanly onto flat report schemas
    return [
        {
            "material_number": lot.material_number,
            "material_name": lot.definition.material_name,
            "lotno": lot.lotno,
            "quantity": lot.quantity,
            "unit": lot.definition.unit
        }
        for lot in lots
    ]
