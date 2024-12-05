from flask import jsonify, request, abort
from service.models import Product, Category
from . import app
from decimal import Decimal

@app.before_request
def check_content_type():
    if request.method in ["POST", "PUT"] and not request.content_type == "application/json":
        return jsonify(message="Content-Type must be application/json"), 415


@app.route("/products", methods=["POST"])
def create_product():
    """Create a new Product"""
    app.logger.info("Request to Create a Product...")
    data = request.get_json()
    product = Product()
    try:
        product.deserialize(data)
        product.create()
        app.logger.info(f"Product with new id [{product.id}] saved!")
        response_data = product.serialize()
        status_code = 201  # HTTP status code for created
    except Exception as e:
        app.logger.error(f"Error creating product: {str(e)}")
        response_data = {"Error creating product": str(e)}
        status_code = 400  # HTTP status code for bad request
    return jsonify(response_data), status_code


@app.route("/products/<int:product_id>", methods=["GET"])
def read_product(product_id):
    """Read a Product by its ID"""
    app.logger.info("Request to read a product with id [%s]", product_id)
    product = Product.find(product_id)
    if not product:
        abort(
            404, f"Product with id '{product_id}' was not found"
        )  # HTTP status code for not found

    app.logger.info("Returning product: %s", product.name)
    return jsonify(product.serialize()), 200


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """Update an existing Product by its ID"""
    app.logger.info("Request to update a product with id %s", product_id)
    product = Product.find(product_id)
    if not product:
        return jsonify(message="Product not found"), 404

    product_data = request.get_json()
    if not product_data:
        return jsonify(message="No data provided"), 400

    try:
        product.deserialize(product_data)
        product.update()
    except Exception as e:
        return jsonify(message=str(e)), 400

    return jsonify(product.serialize()), 200


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Delete a Product by its ID"""
    app.logger.info("Request to delete a product with id %s", product_id)
    product = Product.find(product_id)
    if not product:
        abort(
            404, f"Product with id '{product_id}' was not found"
        )  # HTTP status code for not found
    product.delete()
    return "", 204  # HTTP status code for no content

@app.route("/products", methods=["GET"])
def list_products():
    """List Products by filters"""
    name = request.args.get("name")
    category = request.args.get("category")
    price = request.args.get("price")
    query = Product.query

    if name:
        query = query.filter(Product.name == name)
    
    if category:
        try:
            # Convert category string to enum using the name-based lookup
            category = Category[category.upper()]  # Enum conversion by name
            query = query.filter(Product.category == category)
        except KeyError:
            # Instead of returning a 400 error, simply don't filter by category if invalid
            return jsonify([]), 200
    
    if price:
        try:
            price = Decimal(price)
            query = query.filter(Product.price <= price)
        except ValueError:
            return jsonify(message="Invalid price value"), 400

    products = query.all()
    return jsonify([product.serialize() for product in products]), 200
