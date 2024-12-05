"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""

import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Brand, Category, db
from service import app
from tests.factories import ProductFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:Ma0919213023@localhost:5432/postgres"
)

######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################


class TestProductModel(unittest.TestCase):
    """Test Suite for Product Model"""

    @classmethod
    def setUpClass(cls):
        """Runs once before the entire test suite"""
        app.config["DEBUG"] = False
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        #Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once after the entire test suite"""
        db.session.close()
        with app.app_context():
            db.drop_all()  # Drop all tables to ensure a clean state

    def setUp(self):
        """Runs before each test"""
        db.session.query(Product).delete()  # Clear the Product table from last test
        db.session.commit()

    def tearDown(self):
        """Runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_product(self):
        """Test creating a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Check that it was added to the db
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that the product in the db matches the original product
        found_product = products[0]
        self.assertIsNotNone(found_product)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(Decimal(found_product.price), product.price)
        self.assertEqual(found_product.category, product.category)

    def test_update_product(self):
        """Test updating a product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        new_name = "Updated Name"
        product.name = new_name
        original_id = product.id
        product.update()
        # Fetch it back from db and make sure id hasn't change
        # but the data changed
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(product.name, new_name)

    def test_delete_product(self):
        """Test deleting a product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product from db
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_serialize_product(self):
        """Test serializing a product to a dictionary"""
        product = ProductFactory()
        product_dict = product.serialize()
        self.assertEqual(product_dict["name"], product.name)
        self.assertEqual(product_dict["description"], product.description)
        self.assertEqual(
            product_dict["price"], str(product.price)
        )  # Price should be serialized as a string
        self.assertEqual(product_dict["category"], product.category.name)

    def test_deserialize_product(self):
        """Test deserializing a product from a dictionary"""
        product_data = {
            "name": "Tesla Model S",
            "description": "An electric sedan",
            "price": "79999.99",
            "model_year": 2023,
            "quantity": 5,
            "category": "SEDAN",
        }
        product = Product()
        product.deserialize(product_data)
        self.assertEqual(product.name, product_data["name"])
        self.assertEqual(product.description, product_data["description"])
        self.assertEqual(product.price, Decimal(product_data["price"]))
        self.assertEqual(product.category, Category[product_data["category"]])

    def test_find_all_products(self):
        """Test finding all products in the db"""
        products = Product.all()
        self.assertEqual(products, [])
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # Check that 5 products are added to the database
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """Test finding a product by name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(len(found), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_filters(self):
        """Test finding products with multiple filters"""
        product1 = ProductFactory(
            name="Model Y", category=Category.SUV, price=Decimal("50000.00")
        )
        product1.create()
        product2 = ProductFactory(
            name="Model 3", category=Category.SEDAN, price=Decimal("45000.00")
        )
        product2.create()

        results = Product.find_by_filters(name="Model Y", category=Category.SUV)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Model Y")
        self.assertEqual(results[0].category, Category.SUV)
