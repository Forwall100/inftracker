from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from fastapi import FastAPI, HTTPException, Depends

import uvicorn

# Создаем базу данных SQLite
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модели базы данных
class Category(Base):
    __tablename__ = "categories"  # Указываем имя таблицы
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    unit = Column(String)
    store_urls = Column(String)  # JSON-строка с URL-адресами магазинов
    category = relationship("Category")

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    url = Column(String)

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    store_id = Column(Integer, ForeignKey("stores.id"))
    date = Column(Date)
    price = Column(Float)
    discount_price = Column(Float, nullable=True)
    product = relationship("Product")
    store = relationship("Store")

# Создаем таблицы
Base.metadata.create_all(bind=engine)

# Инициализация FastAPI
app = FastAPI()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD-эндпоинты
@app.post("/categories/")
def create_category(name: str, db: SessionLocal = Depends(get_db)):
    category = Category(name=name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@app.get("/categories/")
def read_categories(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    return db.query(Category).offset(skip).limit(limit).all()

@app.post("/products/")
def create_product(name: str, category_id: int, unit: str, store_urls: str, db: SessionLocal = Depends(get_db)):
    product = Product(name=name, category_id=category_id, unit=unit, store_urls=store_urls)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@app.get("/products/")
def read_products(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    return db.query(Product).offset(skip).limit(limit).all()

@app.post("/stores/")
def create_store(name: str, url: str, db: SessionLocal = Depends(get_db)):
    store = Store(name=name, url=url)
    db.add(store)
    db.commit()
    db.refresh(store)
    return store

@app.get("/stores/")
def read_stores(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    return db.query(Store).offset(skip).limit(limit).all()

@app.post("/prices/")
def create_price(product_id: int, store_id: int, date: str, price: float, discount_price: float = None, db: SessionLocal = Depends(get_db)):
    price_record = Price(product_id=product_id, store_id=store_id, date=date, price=price, discount_price=discount_price)
    db.add(price_record)
    db.commit()
    db.refresh(price_record)
    return price_record

@app.get("/prices/")
def read_prices(skip: int = 0, limit: int = 10, db: SessionLocal = Depends(get_db)):
    return db.query(Price).offset(skip).limit(limit).all()

if __name__ == "__main__":
    uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True)
