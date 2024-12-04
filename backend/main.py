from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, DECIMAL
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, joinedload
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import uvicorn
from datetime import datetime, date

# Импорт парсеров
from parsers.magnit import parse_magnit
from parsers.five import parse_5ka
from parsers.driver_settings import get_driver

# Создание базы данных SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Базовый класс для моделей
Base = declarative_base()

# Модели для таблиц


class Category(Base):
    __tablename__ = "categories"
    CategoryID = Column(Integer, primary_key=True, index=True)
    CategoryName = Column(String, unique=True, index=True)
    Description = Column(String, nullable=True)
    products = relationship("Product", back_populates="category", cascade="all, delete")


class Product(Base):
    __tablename__ = "products"

    ProductID = Column(Integer, primary_key=True, index=True)
    ProductName = Column(String, unique=True, index=True)
    CategoryID = Column(Integer, ForeignKey("categories.CategoryID"))
    ProductLink = Column(String, unique=True)

    category = relationship("Category", back_populates="products")
    prices = relationship("Price", back_populates="product", cascade="all, delete")


class Price(Base):
    __tablename__ = "prices"

    PriceID = Column(Integer, primary_key=True, index=True)
    ProductID = Column(Integer, ForeignKey("products.ProductID"))
    PriceWithDiscount = Column(DECIMAL(10, 2), nullable=True)
    PriceWithoutDiscount = Column(DECIMAL(10, 2), nullable=True)
    PriceDate = Column(Date)

    product = relationship("Product", back_populates="prices")


# Создание сессии и таблиц, если они ещё не созданы
Base.metadata.create_all(bind=engine)

# Модели данных для запросов


class CategoryCreate(BaseModel):
    CategoryName: str
    Description: Optional[str] = None


class ProductCreate(BaseModel):
    ProductName: str
    CategoryID: int
    ProductLink: str


class PriceCreate(BaseModel):
    ProductID: int
    PriceWithDiscount: Optional[float] = None
    PriceWithoutDiscount: Optional[float] = None
    PriceDate: date


# Модели ответов


class CategoryResponse(BaseModel):
    CategoryID: int
    CategoryName: str
    Description: Optional[str] = None

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    ProductID: int
    ProductName: str
    CategoryID: int
    ProductLink: str
    LatestPriceWithDiscount: Optional[float] = None
    LatestPriceWithoutDiscount: Optional[float] = None
    LatestPriceDate: Optional[date] = None

    model_config = {"from_attributes": True}


class PriceResponse(BaseModel):
    PriceID: int
    ProductID: int
    PriceWithDiscount: Optional[float] = None
    PriceWithoutDiscount: Optional[float] = None
    PriceDate: date

    model_config = {"from_attributes": True}


# Новые модели для инфляции


class InflationResponse(BaseModel):
    inflation_percentage: Optional[float] = None
    start_date: date
    end_date: date

    model_config = {"from_attributes": True}


class InflationCategoryResponse(InflationResponse):
    category_id: int
    category_name: str

    model_config = {"from_attributes": True}


class InflationProductResponse(InflationResponse):
    product_id: int
    product_name: str

    model_config = {"from_attributes": True}


class InflationOverallResponse(BaseModel):
    inflation_percentage: Optional[float] = None
    start_date: date
    end_date: date

    model_config = {"from_attributes": True}


class InflationOverallAllTimeResponse(BaseModel):
    inflation_percentage: Optional[float] = None
    observation_period: Optional[str] = "All Time"

    model_config = {"from_attributes": True}


# Создание сессии для работы с БД
def get_db():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Инициализация FastAPI приложения
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Лучше ограничить источники в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Вспомогательные функции
def get_valid_price(price_record: Price) -> Optional[float]:
    """
    Получает валидную цену из записи Price.
    Приоритет отдается PriceWithDiscount, затем PriceWithoutDiscount.
    Возвращает None, если обе цены отсутствуют.
    """
    if price_record.PriceWithDiscount is not None:
        try:
            return float(price_record.PriceWithDiscount)
        except ValueError:
            return None
    elif price_record.PriceWithoutDiscount is not None:
        try:
            return float(price_record.PriceWithoutDiscount)
        except ValueError:
            return None
    return None


def get_price_on_or_before(db: Session, product_id: int, target_date: date):
    """
    Получить последнюю цену продукта на или до заданной даты.
    """
    return (
        db.query(Price)
        .filter(Price.ProductID == product_id, Price.PriceDate <= target_date)
        .order_by(Price.PriceDate.desc())
        .first()
    )


def calculate_inflation(start_price: float, end_price: float) -> Optional[float]:
    """
    Рассчитать процентное изменение цены (инфляцию).
    """
    if start_price == 0:
        return None  # Избегаем деления на ноль
    return ((end_price - start_price) / start_price) * 100


# CRUD операции для Categories


@app.post("/categories/", response_model=CategoryResponse)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # Проверка уникальности CategoryName
    existing_category = (
        db.query(Category)
        .filter(Category.CategoryName == category.CategoryName)
        .first()
    )
    if existing_category:
        raise HTTPException(
            status_code=400, detail="Category with this name already exists"
        )

    db_category = Category(
        CategoryName=category.CategoryName, Description=category.Description
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/categories/", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.CategoryID == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@app.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, updated_category: CategoryCreate, db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.CategoryID == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    # Проверка уникальности CategoryName
    existing_category = (
        db.query(Category)
        .filter(
            Category.CategoryName == updated_category.CategoryName,
            Category.CategoryID != category_id,
        )
        .first()
    )
    if existing_category:
        raise HTTPException(
            status_code=400, detail="Another category with this name already exists"
        )

    db_category.CategoryName = updated_category.CategoryName
    db_category.Description = updated_category.Description
    db.commit()
    db.refresh(db_category)
    return db_category


@app.delete("/categories/{category_id}", response_model=dict)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(Category).filter(Category.CategoryID == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    # Проверка наличия связанных продуктов
    if db_category.products:
        raise HTTPException(
            status_code=400, detail="Cannot delete category with associated products"
        )
    db.delete(db_category)
    db.commit()
    return {"detail": "Category deleted successfully"}


# CRUD операции для Products


@app.post("/products/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Валидация URL
    url = product.ProductLink.lower()
    if "magnit" in url and "5ka" in url:
        raise HTTPException(
            status_code=400,
            detail="URL не должен содержать одновременно 'magnit' и '5ka'",
        )
    elif "magnit" in url:
        parser = parse_magnit
    elif "5ka" in url:
        parser = parse_5ka
    else:
        raise HTTPException(
            status_code=400,
            detail="URL должен содержать 'magnit' или '5ka'",
        )

    # Проверка существования категории
    db_category = (
        db.query(Category).filter(Category.CategoryID == product.CategoryID).first()
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Проверка уникальности ProductLink
    existing_product = (
        db.query(Product).filter(Product.ProductLink == product.ProductLink).first()
    )
    if existing_product:
        raise HTTPException(
            status_code=400, detail="Product with this ProductLink already exists"
        )

    # Создание продукта
    db_product = Product(
        ProductName=product.ProductName,
        CategoryID=product.CategoryID,
        ProductLink=product.ProductLink,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    # Парсинг цены
    try:
        with get_driver() as driver:
            parsed_prices = parser(driver, product.ProductLink)
    except Exception as e:
        # Если парсинг не удался, удаляем созданный продукт
        db.delete(db_product)
        db.commit()
        raise HTTPException(
            status_code=500, detail=f"Ошибка при парсинге цены: {str(e)}"
        )

    # Проверка и создание цены, если данные получены
    price_with_discount = None
    price_without_discount = None
    price_date = None

    if parsed_prices:
        price_with_discount = parsed_prices.get("price_with_discount")
        price_without_discount = parsed_prices.get("price_without_discount")
        if price_with_discount is not None or price_without_discount is not None:
            price_date = (
                datetime.utcnow().date()
            )  # Изменено с isoformat() на date объект
            db_price = Price(
                ProductID=db_product.ProductID,
                PriceWithDiscount=price_with_discount,
                PriceWithoutDiscount=price_without_discount,
                PriceDate=price_date,
            )
            db.add(db_price)
            db.commit()

    return ProductResponse(
        ProductID=db_product.ProductID,
        ProductName=db_product.ProductName,
        CategoryID=db_product.CategoryID,
        ProductLink=db_product.ProductLink,
        LatestPriceWithDiscount=price_with_discount,
        LatestPriceWithoutDiscount=price_without_discount,
        LatestPriceDate=price_date,
    )


@app.get("/products/", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).options(joinedload(Product.prices)).all()
    response = []
    for product in products:
        latest_price = None
        if product.prices:
            latest_price = max(product.prices, key=lambda p: p.PriceDate)
        response.append(
            ProductResponse(
                ProductID=product.ProductID,
                ProductName=product.ProductName,
                CategoryID=product.CategoryID,
                ProductLink=product.ProductLink,
                LatestPriceWithDiscount=(
                    float(latest_price.PriceWithDiscount)
                    if latest_price.PriceWithDiscount
                    else None
                ),
                LatestPriceWithoutDiscount=(
                    float(latest_price.PriceWithoutDiscount)
                    if latest_price.PriceWithoutDiscount
                    else None
                ),
                LatestPriceDate=latest_price.PriceDate if latest_price else None,
            )
        )
    return response


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = (
        db.query(Product)
        .options(joinedload(Product.prices))
        .filter(Product.ProductID == product_id)
        .first()
    )
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    latest_price = None
    if db_product.prices:
        latest_price = max(db_product.prices, key=lambda p: p.PriceDate)

    return ProductResponse(
        ProductID=db_product.ProductID,
        ProductName=db_product.ProductName,
        CategoryID=db_product.CategoryID,
        ProductLink=db_product.ProductLink,
        LatestPriceWithDiscount=(
            float(latest_price.PriceWithDiscount)
            if latest_price.PriceWithDiscount
            else None
        ),
        LatestPriceWithoutDiscount=(
            float(latest_price.PriceWithoutDiscount)
            if latest_price.PriceWithoutDiscount
            else None
        ),
        LatestPriceDate=latest_price.PriceDate if latest_price else None,
    )


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, updated_product: ProductCreate, db: Session = Depends(get_db)
):
    db_product = db.query(Product).filter(Product.ProductID == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Валидация URL
    url = updated_product.ProductLink.lower()
    if "magnit" in url and "5ka" in url:
        raise HTTPException(
            status_code=400,
            detail="URL не должен содержать одновременно 'magnit' и '5ka'",
        )
    elif "magnit" in url:
        parser = parse_magnit
    elif "5ka" in url:
        parser = parse_5ka
    else:
        raise HTTPException(
            status_code=400,
            detail="URL должен содержать 'magnit' или '5ka'",
        )

    # Проверка существования категории
    db_category = (
        db.query(Category)
        .filter(Category.CategoryID == updated_product.CategoryID)
        .first()
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Проверка уникальности ProductLink, если он изменился
    if db_product.ProductLink != updated_product.ProductLink:
        existing_product = (
            db.query(Product)
            .filter(Product.ProductLink == updated_product.ProductLink)
            .first()
        )
        if existing_product:
            raise HTTPException(
                status_code=400,
                detail="Another product with this ProductLink already exists",
            )

    # Обновление продукта
    db_product.ProductName = updated_product.ProductName
    db_product.CategoryID = updated_product.CategoryID
    db_product.ProductLink = updated_product.ProductLink
    db.commit()
    db.refresh(db_product)

    # Парсинг цены
    try:
        with get_driver() as driver:
            parsed_prices = parser(driver, updated_product.ProductLink)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при парсинге цены: {str(e)}"
        )

    # Проверка и создание цены, если данные получены
    price_with_discount = None
    price_without_discount = None
    price_date = None

    if parsed_prices:
        price_with_discount = parsed_prices.get("price_with_discount")
        price_without_discount = parsed_prices.get("price_without_discount")
        if price_with_discount is not None or price_without_discount is not None:
            price_date = datetime.utcnow().date()
            # Получаем последнюю цену для продукта
            db_price = (
                db.query(Price)
                .filter(Price.ProductID == db_product.ProductID)
                .order_by(Price.PriceDate.desc())
                .first()
            )
            if db_price:
                # Обновляем существующую цену
                db_price.PriceWithDiscount = price_with_discount
                db_price.PriceWithoutDiscount = price_without_discount
                db_price.PriceDate = price_date
            else:
                # Создаем новую цену
                db_price = Price(
                    ProductID=db_product.ProductID,
                    PriceWithDiscount=price_with_discount,
                    PriceWithoutDiscount=price_without_discount,
                    PriceDate=price_date,
                )
                db.add(db_price)
            db.commit()

    # Получение последней цены для ответа
    latest_price = None
    if db_product.prices:
        latest_price = max(db_product.prices, key=lambda p: p.PriceDate)

    return ProductResponse(
        ProductID=db_product.ProductID,
        ProductName=db_product.ProductName,
        CategoryID=db_product.CategoryID,
        ProductLink=db_product.ProductLink,
        LatestPriceWithDiscount=(
            float(latest_price.PriceWithDiscount)
            if latest_price.PriceWithDiscount
            else None
        ),
        LatestPriceWithoutDiscount=(
            float(latest_price.PriceWithoutDiscount)
            if latest_price.PriceWithoutDiscount
            else None
        ),
        LatestPriceDate=latest_price.PriceDate if latest_price else None,
    )


@app.delete("/products/{product_id}", response_model=dict)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.ProductID == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted successfully"}


# CRUD операции для Prices


@app.post("/prices/", response_model=PriceResponse)
def create_price(price: PriceCreate, db: Session = Depends(get_db)):
    # Проверка существования продукта
    db_product = db.query(Product).filter(Product.ProductID == price.ProductID).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Создание цены
    db_price = Price(
        ProductID=price.ProductID,
        PriceWithDiscount=price.PriceWithDiscount,
        PriceWithoutDiscount=price.PriceWithoutDiscount,
        PriceDate=price.PriceDate,
    )
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price


@app.get("/prices/", response_model=List[PriceResponse])
def get_prices(db: Session = Depends(get_db)):
    return db.query(Price).all()


@app.get("/prices/{price_id}", response_model=PriceResponse)
def get_price(price_id: int, db: Session = Depends(get_db)):
    db_price = db.query(Price).filter(Price.PriceID == price_id).first()
    if db_price is None:
        raise HTTPException(status_code=404, detail="Price not found")
    return db_price


@app.put("/prices/{price_id}", response_model=PriceResponse)
def update_price(
    price_id: int, updated_price: PriceCreate, db: Session = Depends(get_db)
):
    db_price = db.query(Price).filter(Price.PriceID == price_id).first()
    if db_price is None:
        raise HTTPException(status_code=404, detail="Price not found")

    # Проверка существования продукта
    db_product = (
        db.query(Product).filter(Product.ProductID == updated_price.ProductID).first()
    )
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Обновление цены
    db_price.ProductID = updated_price.ProductID
    db_price.PriceWithDiscount = updated_price.PriceWithDiscount
    db_price.PriceWithoutDiscount = updated_price.PriceWithoutDiscount
    db_price.PriceDate = updated_price.PriceDate
    db.commit()
    db.refresh(db_price)
    return db_price


@app.delete("/prices/{price_id}", response_model=dict)
def delete_price(price_id: int, db: Session = Depends(get_db)):
    db_price = db.query(Price).filter(Price.PriceID == price_id).first()
    if not db_price:
        raise HTTPException(status_code=404, detail="Price not found")
    db.delete(db_price)
    db.commit()
    return {"detail": "Price deleted successfully"}


# Эндпоинты для расчета инфляции


@app.get("/inflation/category/{category_id}", response_model=InflationCategoryResponse)
def get_inflation_by_category(
    category_id: int, start_date: date, end_date: date, db: Session = Depends(get_db)
):
    # Проверка существования категории
    db_category = db.query(Category).filter(Category.CategoryID == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Получение всех продуктов в категории
    products = db.query(Product).filter(Product.CategoryID == category_id).all()
    if not products:
        raise HTTPException(
            status_code=404, detail="No products found in this category"
        )

    inflations = []

    for product in products:
        start_price_record = get_price_on_or_before(db, product.ProductID, start_date)
        end_price_record = get_price_on_or_before(db, product.ProductID, end_date)

        if not start_price_record or not end_price_record:
            continue  # Пропустить, если недостаточно данных

        # Извлечение валидных цен
        start_price = get_valid_price(start_price_record)
        end_price = get_valid_price(end_price_record)

        if start_price is None or end_price is None:
            continue  # Пропустить, если цена отсутствует

        inflation = calculate_inflation(start_price, end_price)
        if inflation is not None:
            inflations.append(inflation)

    if not inflations:
        raise HTTPException(
            status_code=404, detail="Insufficient price data to calculate inflation"
        )

    # Средняя инфляция по категории
    average_inflation = sum(inflations) / len(inflations)

    return InflationCategoryResponse(
        inflation_percentage=round(average_inflation, 2),
        start_date=start_date,
        end_date=end_date,
        category_id=db_category.CategoryID,
        category_name=db_category.CategoryName,
    )


@app.get("/inflation/product/{product_id}", response_model=InflationProductResponse)
def get_inflation_by_product(
    product_id: int, start_date: date, end_date: date, db: Session = Depends(get_db)
):
    # Проверка существования продукта
    db_product = db.query(Product).filter(Product.ProductID == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    start_price_record = get_price_on_or_before(db, product_id, start_date)
    end_price_record = get_price_on_or_before(db, product_id, end_date)

    if not start_price_record or not end_price_record:
        raise HTTPException(
            status_code=404, detail="Insufficient price data to calculate inflation"
        )

    # Извлечение валидных цен
    start_price = get_valid_price(start_price_record)
    end_price = get_valid_price(end_price_record)

    if start_price is None or end_price is None:
        raise HTTPException(
            status_code=400, detail="Insufficient price data for inflation calculation"
        )

    inflation = calculate_inflation(start_price, end_price)
    if inflation is None:
        raise HTTPException(
            status_code=400, detail="Cannot calculate inflation due to zero start price"
        )

    return InflationProductResponse(
        inflation_percentage=round(inflation, 2),
        start_date=start_date,
        end_date=end_date,
        product_id=db_product.ProductID,
        product_name=db_product.ProductName,
    )


@app.get("/inflation/overall", response_model=InflationOverallResponse)
def get_overall_inflation(
    start_date: date, end_date: date, db: Session = Depends(get_db)
):
    products = db.query(Product).all()
    if not products:
        raise HTTPException(status_code=404, detail="No products found")

    inflations = []

    for product in products:
        start_price_record = get_price_on_or_before(db, product.ProductID, start_date)
        end_price_record = get_price_on_or_before(db, product.ProductID, end_date)

        if not start_price_record or not end_price_record:
            continue  # Пропустить, если недостаточно данных

        # Извлечение валидных цен
        start_price = get_valid_price(start_price_record)
        end_price = get_valid_price(end_price_record)

        if start_price is None or end_price is None:
            continue  # Пропустить, если цена отсутствует

        inflation = calculate_inflation(start_price, end_price)
        if inflation is not None:
            inflations.append(inflation)

    if not inflations:
        raise HTTPException(
            status_code=404,
            detail="Insufficient price data to calculate overall inflation",
        )

    # Средняя инфляция по всем продуктам
    average_inflation = sum(inflations) / len(inflations)

    return InflationOverallResponse(
        inflation_percentage=round(average_inflation, 2),
        start_date=start_date,
        end_date=end_date,
    )


@app.get("/inflation/overall/all_time", response_model=InflationOverallAllTimeResponse)
def get_overall_inflation_all_time(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    if not products:
        raise HTTPException(status_code=404, detail="No products found")

    inflations = []

    for product in products:
        # Получение самой ранней и самой поздней цены
        earliest_price_record = (
            db.query(Price)
            .filter(Price.ProductID == product.ProductID)
            .order_by(Price.PriceDate.asc())
            .first()
        )
        latest_price_record = (
            db.query(Price)
            .filter(Price.ProductID == product.ProductID)
            .order_by(Price.PriceDate.desc())
            .first()
        )

        if not earliest_price_record or not latest_price_record:
            continue 

        # Извлечение валидных цен
        start_price = get_valid_price(earliest_price_record)
        end_price = get_valid_price(latest_price_record)

        if start_price is None or end_price is None:
            continue  # Пропустить, если цена отсутствует

        inflation = calculate_inflation(start_price, end_price)
        if inflation is not None:
            inflations.append(inflation)

    if not inflations:
        raise HTTPException(
            status_code=404,
            detail="Insufficient price data to calculate overall inflation",
        )

    # Средняя инфляция по всем продуктам
    average_inflation = sum(inflations) / len(inflations)

    return InflationOverallAllTimeResponse(
        inflation_percentage=round(average_inflation, 2), observation_period="All Time"
    )


# Запуск FastAPI сервера, если запускается основной скрипт
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
