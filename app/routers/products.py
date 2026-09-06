from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app import schemas
from app.models import ProductRecipe, MaterialDefinition, ProductDefinition, ProductLog, MaterialLot
from app.schemas import CreateRecipeRequest, RecipeRequirementReport
from app.crud import products as crud

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/catalog/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def register_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Registers a permanent product code profile with its assigned customers."""
    if crud.get_product_by_code(db, product.product_code):
        raise HTTPException(status_code=400, detail="Product code already registered")
    return crud.create_product_definition(db, product)

# 1. Define the recipe rules (e.g., 1 Product ABC requires 1 Material A and 2 Material B)
@router.post("/recipe/", status_code=status.HTTP_201_CREATED)
def save_product_recipe(payload: CreateRecipeRequest, db: Session = Depends(get_db)):
    """Saves or overwrites the required raw materials mixture ratio for a product."""
    # Verify product exists
    product = db.query(ProductDefinition).filter(ProductDefinition.product_code == payload.product_code).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product code not found")

    # Clear out any old recipe choices for this product to prevent duplication anomalies
    db.query(ProductRecipe).filter(ProductRecipe.product_code == payload.product_code).delete()

    # Save the new recipe ingredients link rows
    for item in payload.ingredients:
        # Verify material exists
        material = db.query(MaterialDefinition).filter(MaterialDefinition.material_number == item.material_number).first()
        if not material:
            raise HTTPException(status_code=404, detail=f"Material code {item.material_number} does not exist")
            
        new_recipe_row = ProductRecipe(
            product_code=payload.product_code,
            material_number=item.material_number,
            required_quantity=item.required_quantity
        )
        db.add(new_recipe_row)
        
    db.commit()
    return {"message": f"Recipe rules saved successfully for product {payload.product_code}"}


# 2. RUN THE CALCULATION: Input the target quantity, get the required materials back
@router.get("/recipe/calculate/{product_code}", response_model=list[RecipeRequirementReport])
def calculate_required_materials(product_code: str, build_quantity: float, db: Session = Depends(get_db)):
    """Calculates exactly how much material is needed to build a target amount of a product."""
    # Fetch recipe structure
    recipe_items = db.query(ProductRecipe).filter(ProductRecipe.product_code == product_code).all()
    if not recipe_items:
        raise HTTPException(status_code=404, detail="No recipe blueprint rules configured for this product")

    report = []
    for item in recipe_items:
        # Calculate dynamic requirement balances
        total_needed = item.required_quantity * build_quantity
        
        report.append({
            "material_number": item.material_number,
            "material_name": item.material.material_name,  # Fetched via table relationship
            "unit": item.material.unit,                    # Fetched via table relationship
            "quantity_needed_per_unit": item.required_quantity,
            "total_quantity_needed": total_needed
        })
        
    return report


@router.post("/log/", status_code=status.HTTP_201_CREATED)
def add_product_quantity(log_data: schemas.ProductLogCreate, db: Session = Depends(get_db)):
    """Logs product creation and automatically calculates and deducts raw materials from warehouse inventory."""
    # 1. Verify the product exists in the master catalog
    product = db.query(ProductDefinition).filter(ProductDefinition.product_code == log_data.product_code).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product blueprint code not found")

    # 2. Check if a manufacturing recipe exists for this product
    recipe_items = db.query(ProductRecipe).filter(ProductRecipe.product_code == log_data.product_code).all()
    if not recipe_items:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot log production. No recipe rule configured for product '{log_data.product_code}'."
        )

    # 3. FIRST PASS: Check if you have enough warehouse inventory before deducting anything
    for item in recipe_items:
        total_material_needed = item.required_quantity * log_data.quantity
        
        # Calculate total available stock across all lots for this material
        total_available_stock = db.query(func.sum(MaterialLot.quantity)).filter(
            MaterialLot.material_number == item.material_number
        ).scalar() or 0.0

        if total_available_stock < total_material_needed:
            raise HTTPException(
                status_code=400,
                detail=f"Incomplete Inventory. Need {total_material_needed} of material '{item.material_number}', but only {total_available_stock} exists in stock."
            )

    # 4. SECOND PASS: Deduct raw materials from stock (FIFO style: oldest lots first)
    for item in recipe_items:
        remaining_to_deduct = item.required_quantity * log_data.quantity
        
        # Fetch available lots for this material, ordered by id (oldest tracking rows first)
        active_lots = db.query(MaterialLot).filter(
            MaterialLot.material_number == item.material_number,
            MaterialLot.quantity > 0
        ).order_by(MaterialLot.id.asc()).all()

        for lot in active_lots:
            if remaining_to_deduct <= 0:
                break
                
            if lot.quantity >= remaining_to_deduct:
                # This lot has enough to fulfill the remaining balance completely
                lot.quantity -= remaining_to_deduct
                remaining_to_deduct = 0
            else:
                # Empty this lot out entirely and move to the next one
                remaining_to_deduct -= lot.quantity
                lot.quantity = 0.0

    # 5. Record the final production entry into the product transaction ledger
    new_log = ProductLog(
        product_code=log_data.product_code,
        date=log_data.date,
        quantity=log_data.quantity
    )
    db.add(new_log)
    
    # Commit all inventory deductions and the product log entry together as a safe single action
    db.commit()
    db.refresh(new_log)
    
    return {
        "status": "Success",
        "message": f"Logged {log_data.quantity} units of {log_data.product_code}.",
        "inventory": "Required raw materials calculated and deducted from warehouse storage."
    }

@router.get("/ledger/", response_model=list[schemas.ProductLedgerReport])
def view_full_product_ledger(db: Session = Depends(get_db)):
    """Retrieves full item tracking transaction sheet along with customer associations."""
    logs = crud.get_all_product_logs(db)
    return [
        {
            "product_code": log.product_code,
            "product_name": log.definition.product_name,
            "part_number": log.definition.part_number,
            "customers": log.definition.customers,
            "date": log.date,
            "quantity": log.quantity
        }
        for log in logs
    ]



