import os
import logging
from unittest import TestCase
from decimal import Decimal
from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:Ma0919213023@localhost:5432/postgres"
)

BASE_URL = "/products"


class TestProductRoutes(TestCase):
    """Test Cases for Product Routes"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        cls.client = app.test_client()
        #init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()
        with app.app_context():
            db.drop_all()

    def setUp(self):
        """This runs before each test"""
        with app.app_context():
            db.session.query(Product).delete()
            db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ############################################################
    #  T E S T   C A S E S
    ############################################################

    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        # Check it was created correctly
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.get_json()
        self.assertEqual(data["name"], test_product.name)
        self.assertEqual(Decimal(data["price"]), test_product.price)
        self.assertEqual(data["brand"], test_product.brand.name)

    def test_read_product(self):
        """It should Read a Product by ID"""
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product_id = response.get_json()["id"]
        response = self.client.get(f"{BASE_URL}/{product_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_product.name)

    def test_update_product(self):
        """It should Update a Product"""
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Update the product
        new_product = response.get_json()
        new_product["name"] = "unknown"
        response = self.client.put(f"{BASE_URL}/{new_product['id']}", json=new_product)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "unknown")
        

    def test_delete_product(self):
        """It should Delete a Product by ID"""
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product_id = response.get_json()["id"]
        response = self.client.delete(f"{BASE_URL}/{product_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    def test_list_all_products(self):
        """It should List all Products"""
        self.client.post(BASE_URL, json=ProductFactory().serialize())
        self.client.post(BASE_URL, json=ProductFactory().serialize())
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)

    def test_list_products_by_name(self):
        """It should List Products by Name"""
        product_x = ProductFactory(name="Car X")
        product_y = ProductFactory(name="Car Y")
        self.client.post(BASE_URL, json=product_x.serialize())
        self.client.post(BASE_URL, json=product_y.serialize())
        response = self.client.get(f"{BASE_URL}?name=Car X")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Car X")

    def test_list_products_by_filters(self):
        """It should List Products by Filters"""
        product_a = ProductFactory(
            name="Car A", category=Category.SUV, price=Decimal("30000.00")
        )
        product_b = ProductFactory(
            name="Car B", category=Category.SEDAN, price=Decimal("25000.00")
        )
        product_c = ProductFactory(
            name="Car C", category=Category.SUV, price=Decimal("35000.00")
        )

        self.client.post(BASE_URL, json=product_a.serialize())
        self.client.post(BASE_URL, json=product_b.serialize())
        self.client.post(BASE_URL, json=product_c.serialize())

        # Filter by category (SUV)
        response = self.client.get(f"{BASE_URL}?category=SUV")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        self.assertTrue(all(item["category"] == "SUV" for item in data))

        # Filter by price (<= 30000)
        response = self.client.get(f"{BASE_URL}?price=30000.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        self.assertTrue(
            all(Decimal(item["price"]) <= Decimal("30000.00") for item in data)
        )

        # Filter by name (Car B)
        response = self.client.get(f"{BASE_URL}?name=Car B")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Car B")

        # Chaining filters (category=SUV, price<=35000)
        response = self.client.get(f"{BASE_URL}?category=SUV&price=35000.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        self.assertTrue(
            all(
                item["category"] == "SUV"
                and Decimal(item["price"]) <= Decimal("35000.00")
                for item in data
            )
        )

    ############################################################
    #  UNHAPPY T E S T   C A S E S
    ############################################################
    def test_create_product_with_missing_name(self):
        """It should not Create a Product without a name"""
        test_product = ProductFactory()
        product_data = test_product.serialize()
        del product_data["name"]
        response = self.client.post(BASE_URL, json=product_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_nonexistent_product(self):
        """It should not Read a Product that does not exist"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_nonexistent_product(self):
        """It should not Update a Product that does not exist"""
        update_data = {
            "name": "Nonexistent Product",
            "description": "This product does not exist",
        }
        response = self.client.put(f"{BASE_URL}/0", json=update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_product(self):
        """It should not Delete a Product that does not exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        test_product = ProductFactory()
        response = self.client.post(
            BASE_URL, json=test_product.serialize(), content_type="text/plain"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        test_product = ProductFactory()
        response = self.client.post(BASE_URL, data=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_list_products_by_filters_unhappy_path(self):
        """It should return an empty list when no products match the filters"""
        product_a = ProductFactory(
            name="Car A", category=Category.SUV, price=Decimal("30000.00")
        )
        product_b = ProductFactory(
            name="Car B", category=Category.SEDAN, price=Decimal("25000.00")
        )
        self.client.post(BASE_URL, json=product_a.serialize())
        self.client.post(BASE_URL, json=product_b.serialize())

        # Filter by category that does not exist
        response = self.client.get(f"{BASE_URL}?category=TRUCK")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 0)

        # Chaining filters with no matches (category=SUV, price<=20000)
        response = self.client.get(f"{BASE_URL}?category=SUV&price=20000.00")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 0)
