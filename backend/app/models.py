from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import date

#Registering materials
class MaterialDefinition(Base):
    __tablename__ = "material_definitions"

    id = Column(Integer, primary_key=True, index=True)
    material_number = Column(String, unique=True, index=True, nullable=False)
    material_name = Column(String, index=True, nullable=False)
    part_no = Column(String, index=True, nullable=True)
    type = Column(String, index=True, nullable=True)  # Optional type/category  
    unit = Column(String, default="pcs", nullable=False)

    # Establish relationship to inventory lots
    lots = relationship("MaterialLot", back_populates="definition", cascade="all, delete-orphan")


class MaterialLot(Base):
    __tablename__ = "material_lots"

    id = Column(Integer, primary_key=True, index=True)
    material_number = Column(String, ForeignKey("material_definitions.material_number", onupdate="CASCADE"), nullable=False)
    lotno = Column(String, index=True, nullable=False)
    type = Column(String, index=True, nullable=True)  # Optional type/category
    quantity = Column(Float, default=0.0, nullable=False)

    # Relationship back to master item info
    definition = relationship("MaterialDefinition", back_populates="lots")


#Registering Products
class ProductDefinition(Base):
    __tablename__ = "product_definitions"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, unique=True, index=True, nullable=False)
    product_name = Column(String, index=True, nullable=False)
    part_number = Column(String, index=True, nullable=True)  # Optional ("for some")
    type = Column(String, index=True, nullable=True)  # Optional type/category
    customers = Column(ARRAY(String), nullable=False)        # Stores list of customer names

    # Connects to tracking history
    history = relationship("ProductLog", back_populates="definition", cascade="all, delete-orphan")


class ProductLog(Base):
    __tablename__ = "product_logs"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, ForeignKey("product_definitions.product_code", onupdate="CASCADE"), nullable=False)
    date = Column(Date, index=True, nullable=False)          # Tracks transaction date
    quantity = Column(Float, nullable=False)

    # Link back to master product info
    definition = relationship("ProductDefinition", back_populates="history")


#Product and Materials relationship
class ProductRecipe(Base):
    __tablename__ = "product_recipes"

    id = Column(Integer, primary_key=True, index=True)
    # Links to the product being made
    product_code = Column(String, ForeignKey("product_definitions.product_code", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    # Links to the required raw material
    material_number = Column(String, ForeignKey("material_definitions.material_number", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)
    # How much raw material is needed for exactly 1 unit of this product
    required_quantity = Column(Float, nullable=False)

    # Establish relationships for easy data lookup
    product = relationship("ProductDefinition")
    material = relationship("MaterialDefinition")

class ProductionMaterial(Base):
    __tablename__ = "production_line_materials"

    id = Column(Integer, primary_key=True, index=True)
    lot_number = Column(String, nullable=False)
    # lot_number = Column(String, ForeignKey("material_lots.lotno"), nullable=False)
    material_number = Column(String,ForeignKey("material_definitions.material_number"), nullable=False)
    quantity = Column(Float, default=0.0)
    material = relationship("MaterialDefinition")
    lot = relationship(
        "MaterialLot",
        primaryjoin="ProductionMaterial.lot_number == MaterialLot.lotno",
        foreign_keys=[lot_number],
        uselist=False  # Set to True if multiple lots can share the lotno string
    )