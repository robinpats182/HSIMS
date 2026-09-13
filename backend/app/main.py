from fastapi import FastAPI
from app.database import engine, Base
from app.routers import materials, products, production

# Build database tables automatically on launch
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI Modular Warehouse Backend")

# Register your feature router
app.include_router(materials.router)
app.include_router(production.router)
app.include_router(products.router)

@app.get("/")
def health_check():
    return {"status": "healthy", "architecture": "modular"}
