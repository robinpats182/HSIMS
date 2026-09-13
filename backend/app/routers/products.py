from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.models import ProductRecipe, MaterialDefinition, ProductDefinition, ProductLog, MaterialLot
from app.schemas import CreateRecipeRequest, RecipeRequirementReport
from app.crud import products as crud   
from app.crud import production as production_crud

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
    """Logs product creation and deducts materials from production line stock using FIFO (smallest lot number first)."""
    # 1. Verify product exists
    if not crud.get_product_by_code(db, log_data.product_code):
        raise HTTPException(status_code=404, detail="Product blueprint code not found")

    # 2. Fetch product recipe
    recipe_items = crud.get_product_recipe(db, log_data.product_code)
    if not recipe_items:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot log production. No recipe rule configured for product '{log_data.product_code}'."
        )

    # 3. PASS 1: Check total line stock across all lots
    for item in recipe_items:
        total_needed = item.required_quantity * log_data.quantity
        available_qty = crud.get_total_production_material_quantity(db, item.material_number)

        if available_qty < total_needed:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Incomplete Inventory. Need {total_needed} of material '{item.material_number}', "
                    f"but only {available_qty} is available on the production line."
                )
            )

    # 4. PASS 2: Deduct materials using FIFO (smallest lot_number first)
    for item in recipe_items:
        total_needed = item.required_quantity * log_data.quantity
        crud.deduct_production_materials_fifo(db, item.material_number, total_needed)

    # 5. Create product log entry and commit atomic transaction
    new_log = crud.create_product_log(db, log_data)
    db.commit()
    db.refresh(new_log)

    return {
        "status": "Success",
        "message": f"Logged {log_data.quantity} units of {log_data.product_code}.",
        "inventory": "Required raw materials deducted from production line using FIFO (smallest lot number first)."
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



