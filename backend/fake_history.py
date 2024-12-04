# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Date, DECIMAL
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

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

# generate_price_history.py
import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

# Параметры
DATABASE_URL = "sqlite:///./test.db"  # Замените на ваш путь к базе данных
PRICE_CHANGE_PERCENT = 0.05  # Максимальное изменение цены (5%)
FREQUENCY_DAYS = 7  # Периодичность генерации цен (еженедельно)

def get_engine(db_url=DATABASE_URL):
    return create_engine(db_url, connect_args={"check_same_thread": False})

def create_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

def generate_price_history():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    # Убедитесь, что таблицы существуют
    Base.metadata.create_all(engine)

    try:
        products = session.query(Product).options(joinedload(Product.prices)).all()
        today = datetime.utcnow().date()
        one_year_ago = today - timedelta(days=365)

        for product in products:
            # Получаем последнюю цену
            if not product.prices:
                print(f"Продукт '{product.ProductName}' не имеет записей о ценах. Пропуск.")
                continue

            latest_price = max(product.prices, key=lambda p: p.PriceDate)
            latest_date = latest_price.PriceDate

            # Проверяем, что последняя цена не старше сегодняшней даты
            if latest_date > today:
                print(f"Последняя дата цены для продукта '{product.ProductName}' позже сегодняшней. Пропуск.")
                continue

            # Если последняя цена уже на сегодня, начинаем с прошлой даты
            if latest_date == today:
                current_date = latest_date - timedelta(days=FREQUENCY_DAYS)
                current_price_with_discount = float(latest_price.PriceWithDiscount) if latest_price.PriceWithDiscount else 100.0
                current_price_without_discount = float(latest_price.PriceWithoutDiscount) if latest_price.PriceWithoutDiscount else 120.0
            else:
                current_date = latest_date
                current_price_with_discount = float(latest_price.PriceWithDiscount) if latest_price.PriceWithDiscount else 100.0
                current_price_without_discount = float(latest_price.PriceWithoutDiscount) if latest_price.PriceWithoutDiscount else 120.0

            # Генерация цен назад по времени до one_year_ago
            while current_date > one_year_ago:
                # Случайное изменение цены в пределах ±PRICE_CHANGE_PERCENT
                change_factor = 1 + random.uniform(-PRICE_CHANGE_PERCENT, PRICE_CHANGE_PERCENT)
                new_price_with_discount = Decimal(current_price_with_discount * change_factor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                new_price_without_discount = Decimal(current_price_without_discount * change_factor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                # Новый дата
                new_date = current_date - timedelta(days=FREQUENCY_DAYS)
                if new_date < one_year_ago:
                    new_date = one_year_ago

                # Проверка, существует ли уже цена на эту дату
                existing_price = session.query(Price).filter(
                    Price.ProductID == product.ProductID,
                    Price.PriceDate == new_date
                ).first()
                if existing_price:
                    print(f"Цена на дату {new_date} для продукта '{product.ProductName}' уже существует. Пропуск.")
                else:
                    # Создание новой записи о цене
                    new_price = Price(
                        ProductID=product.ProductID,
                        PriceWithDiscount=new_price_with_discount,
                        PriceWithoutDiscount=new_price_without_discount,
                        PriceDate=new_date
                    )
                    session.add(new_price)
                    print(f"Добавлена цена для '{product.ProductName}' на {new_date}: со скидкой {new_price_with_discount} ₽, без скидки {new_price_without_discount} ₽")

                # Обновляем текущую цену и дату для следующего шага
                current_price_with_discount = float(new_price_with_discount)
                current_price_without_discount = float(new_price_without_discount)
                current_date = new_date

        session.commit()
        print("История цен успешно сгенерирована.")
    except Exception as e:
        session.rollback()
        print(f"Произошла ошибка: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    generate_price_history()
