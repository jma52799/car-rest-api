"""
Models for Car Catalog 

Models:
------
Product - A product in the car catalog

Attributes:
----------
name (string) - the name of the car
brand (string) - the brand of the product
category (enum) - category of the car (e.g: suv, sedan, electric, hybrid)
description (string) - a description of the product
price (numeric) - the selling price of the product
model_year () - the year the product was made
quantity () - the remaining quantity of the product in the catalog

"""

import logging
from enum import Enum
from decimal import Decimal
from typing import Optional
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

db = SQLAlchemy()


def init_db(app):
    Product.init_db(app)
    """
    Order.init_db(app)
    Customer.init_db(app)
    """


class DataValidationError(Exception):
    """Custom Exception for data validation errors"""

    def __init__(self, message):
        super().__init__(message)


class Brand(Enum):
    UNKNOWN = 0
    TOYOTA = 1
    HONDA = 2
    FORD = 3
    CHEVROLET = 4
    BMW = 5
    MERCEDES = 6
    AUDI = 7
    TESLA = 8
    VOLKSWAGEN = 9
    NISSAN = 10


class Category(Enum):
    UNKNOWN = 0
    SUV = 1
    SEDAN = 2
    SPORTS = 3


class Product(db.Model):
    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.Enum(Brand), nullable=False, server_default=Brand.UNKNOWN.name)

    category = db.Column(
        db.Enum(Category), nullable=False, server_default=Category.UNKNOWN.name
    )
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    model_year = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    ##################################################
    # Instance Methods
    ##################################################
    def __repr__(self):
        return f"<Product {self.name}, Brand: {self.brand}, Year: {self.model_year}>"

    def create(self):
        """
        Creates a Product in the database
        """
        self.id = None
        db.session.add(self)
        db.session.commit()
        logger.info(f"Creating Product {self} to database")

    def update(self):
        """
        Updates a Product in the database
        """
        if not self.id:
            raise DataValidationError("Update called on a Product with empty Id field")
        db.session.commit()
        logger.info(f"Updated Product in database: {self}")

    def delete(self):
        """
        Deletes a Product from the database
        """
        db.session.delete(self)
        db.session.commit()
        logger.info(f"Deleted Product from database: {self}")

    def serialize(self) -> dict:
        """Serialize a Product into a dict"""
        serialized_data = {
            "id": self.id,
            "name": self.name,
            "brand": self.brand.name,
            "category": self.category.name,
            "description": self.description,
            "price": str(self.price),
            "model_year": self.model_year,
            "quantity": self.quantity,
        }
        return serialized_data

    def deserialize(self, data: dict):
        """
        Deserializes a Product from a dictionary
        Args:
            data (dict): A dictionary containing the Product data
        """
        try:
            # Required fields
            self.name = data["name"]
            self.description = data["description"]
            self.price = Decimal(data["price"])
            self.model_year = data["model_year"]
            self.quantity = data["quantity"]

            # Brand field - validate as Enum
            if "brand" in data:
                if data["brand"] in Brand.__members__:
                    self.brand = Brand[data["brand"]]
                else:
                    raise DataValidationError(f"Invalid brand: {data['brand']}")

            # Category field - validate as Enum
            if "category" in data:
                if data["category"] in Category.__members__:
                    self.category = Category[data["category"]]
                else:
                    raise DataValidationError(f"Invalid category: {data['category']}")

        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid product: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid product: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def init_db(cls, app: Flask):
        """Initializes the database session

        :param app: the Flask app
        :type data: Flask

        """
        logger.info("Initializing database")
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls) -> list:
        """Returns all of the Products in the database"""
        logger.info("Processing all Products")
        return cls.query.all()
    
    @classmethod
    def find(cls, product_id: int):
        '''Find a product by id'''
        return db.session.get(cls, product_id)

    @classmethod
    def find_by_name(cls, name: str) -> list:
        """Returns all Products with the given name

        :param name: the name of the Products you want to match
        :type name: str

        :return: a collection of Products with that name
        :rtype: list

        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name).all()

    @classmethod
    def find_by_filters(
        cls,
        name: Optional[str] = None,
        price: Optional[Decimal] = None,
        category: Optional[Category] = None,
    ) -> list:
        """Finds Products by multiple optional filters

        Args:
            name (str, optional): The name of the product.
            price (Decimal, optional): The price of the product.
            category (Category, optional): The category of the product.

        Returns:
            list: A list of Product instances that match the given filters.
        """
        logger.info("Searching for products with provided filters.")

        # Start the query from the Product model
        query = cls.query

        # Apply filters conditionally
        if name:
            query = query.filter(cls.name == name)
        if price:
            query = query.filter(cls.price == price)
        if category:
            query = query.filter(cls.category == category)

        # Execute the query and return the results as a list
        return query.all()
