from sqlalchemy.orm import Session
from app.models import ProductDefinition, ProductLog
from app import schemas

def get_product_by_code(db: Session, product_code: str):
    return db.query(ProductDefinition).filter(ProductDefinition.product_code == product_code).first()

def create_product_definition(db: Session, product: schemas.ProductCreate):
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

def log_product_transaction(db: Session, log_data: schemas.ProductLogCreate):
    new_log = ProductLog(
        product_code=log_data.product_code,
        date=log_data.date,
        quantity=log_data.quantity
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log

def get_all_product_logs(db: Session):
    return db.query(ProductLog).all()
