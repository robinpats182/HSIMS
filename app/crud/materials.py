from sqlalchemy.orm import Session
from app.models import MaterialDefinition, MaterialLot
from app.schemas import CatalogCreate, CatalogUpdate, LotCreate

# --- CATALOG CRUD ---
def get_catalog_by_number(db: Session, material_number: str):
    return db.query(MaterialDefinition).filter(MaterialDefinition.material_number == material_number).first()

def get_all_catalog_items(db: Session):
    """Fetches all master material definitions from the catalog."""
    return db.query(MaterialDefinition).all()

def get_catalog_by_name(db: Session, material_name: str):
    return db.query(MaterialDefinition).filter(MaterialDefinition.material_name == material_name).first()

def create_catalog_item(db: Session, item: CatalogCreate):
    db_item = MaterialDefinition(
        material_number=item.material_number,
        material_name=item.material_name,
        unit=item.unit.lower()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_catalog_item(db: Session, db_item: MaterialDefinition, updates: CatalogUpdate):
    if updates.material_name is not None:
        db_item.material_name = updates.material_name
    if updates.unit is not None:
        db_item.unit = updates.unit.lower()
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_catalog_item(db: Session, db_item: MaterialDefinition):
    db.delete(db_item)
    db.commit()

# --- INVENTORY CRUD ---
def get_lot(db: Session, material_number: str, lotno: str):
    return db.query(MaterialLot).filter(
        MaterialLot.material_number == material_number,
        MaterialLot.lotno == lotno
    ).first()

def receive_inventory_lot(db: Session, lot_data: LotCreate):
    existing_lot = get_lot(db, lot_data.material_number, lot_data.lotno)
    
    if existing_lot:
        existing_lot.quantity += lot_data.quantity
        db.commit()
        db.refresh(existing_lot)
        return existing_lot
    else:
        new_lot = MaterialLot(
            material_number=lot_data.material_number,
            lotno=lot_data.lotno,
            quantity=lot_data.quantity
        )
        db.add(new_lot)
        db.commit()
        db.refresh(new_lot)
        return new_lot

def set_lot_balance(db: Session, db_lot: MaterialLot, new_quantity: float):
    db_lot.quantity = new_quantity
    db.commit()
    db.refresh(db_lot)
    return db_lot

def delete_lot_record(db: Session, db_lot: MaterialLot):
    db.delete(db_lot)
    db.commit()

def get_all_warehouse_stock(db: Session):
    return db.query(MaterialLot).all()
