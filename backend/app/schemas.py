import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

# --- CATALOG SCHEMAS ---
class CatalogBase(BaseModel):
    material_number: str = Field(..., min_length=1, description="Unique material identifier")
    material_name: str = Field(..., min_length=1, description="Descriptive name")
    part_no: str | None = Field(None, description="Optional internal/customer part number")
    type: Optional[Literal["LHD", "RHD", "CCW", "CW"]] = None
    @field_validator("type", mode="before")
    @classmethod
    def uppercase_type(cls, value: str):
        if isinstance(value, str):
            return value.upper()  # Forces incoming text (like "lhs" or "Lhs") to "LHS"
        return value
    
    unit: Literal["pcs", "g", "kg"] = "pcs"

class CatalogCreate(CatalogBase):
    pass

class CatalogUpdate(BaseModel):
    material_name: str | None = None
    part_no: str | None = None
    type: Optional[Literal["LHD", "RHD", "CCW", "CW"]] = None
    @field_validator("type", mode="before")
    @classmethod
    def uppercase_type(cls, value: str):
        if isinstance(value, str):
            return value.upper()  # Forces incoming text (like "lhs" or "Lhs") to "LHS"
        return value
    unit: Literal["pcs", "g", "kg"] | None = None

class CatalogResponse(CatalogBase):
    id: int

    class Config:
        from_attributes = True


# --- INVENTORY SCHEMAS ---
class LotBase(BaseModel):
    material_number: str
    lotno: str
    quantity: float = Field(..., ge=0, description="Quantity cannot be negative")

class LotCreate(LotBase):
    pass

class LotUpdate(BaseModel):
    quantity: float = Field(..., ge=0)

# Combined response layout for full warehouse reports
class WarehouseStockReport(BaseModel):
    material_number: str
    material_name: str
    lotno: str
    quantity: float
    unit: str

    class Config:
        from_attributes = True


# --- PRODUCT MASTER CATALOG ---
class ProductCreate(BaseModel):
    product_code: str = Field(..., description="Unique product system code")
    product_name: str = Field(..., description="Name of the product")
    part_number: str | None = Field(None, description="Optional internal/customer part number")
    customers: list[str] = Field(..., description="List of associated customers (e.g. ['Customer A', 'Customer B'])")

class ProductResponse(ProductCreate):
    id: int
    class Config:
        from_attributes = True

# --- PRODUCT TRANSACTION LOGS ---
class ProductLogCreate(BaseModel):
    product_code: str
    date: datetime.date = Field(default_factory=datetime.date.today, description="YYYY-MM-DD transaction date")
    quantity: float

class ProductLedgerReport(BaseModel):
    product_code: str
    product_name: str
    part_number: str | None
    customers: list[str]
    date: datetime.date
    quantity: float
    class Config:
        from_attributes = True


# --- RECIPE SCHEMAS ---
class RecipeItem(BaseModel):
    material_number: str = Field(..., description="Material code needed")
    required_quantity: float = Field(..., gt=0, description="Amount needed for 1 finished product")

class CreateRecipeRequest(BaseModel):
    product_code: str
    ingredients: list[RecipeItem]

class RecipeRequirementReport(BaseModel):
    material_number: str
    material_name: str
    unit: str
    quantity_needed_per_unit: float
    total_quantity_needed: float

# --- Production Line ---
class ProductionMaterialCreate(BaseModel):
    material_number: str
    lot_number: str
    quantity: float


class ProductionMaterialUpdate(BaseModel):
    quantity: float


class ProductionMaterialResponse(BaseModel):
    id: int
    material_number: str
    material_name: str
    lot_number: str
    quantity: float
    unit: str

    class Config:
        from_attributes = True

class ProductionStockReport(BaseModel):
    material_number: str
    material_name: str
    lot_number: str
    quantity: float
    unit: str