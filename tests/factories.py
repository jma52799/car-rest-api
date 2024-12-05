import factory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal
from service.models import Product, Category, Brand


class ProductFactory(factory.Factory):
    """Creates fake products for testing"""

    class Meta:
        """Maps factory to data model"""

        model = Product

    id = factory.Sequence(lambda n: n)
    name = FuzzyChoice(
        choices=[
            "Model S",
            "Model X",
            "Model 3",
            "Mustang",
            "Camry",
            "Civic",
            "Accord",
            "Explorer",
            "Highlander",
            "Leaf",
        ]
    )
    description = factory.Faker("text")
    price = FuzzyDecimal(10000.0, 100000.0, 2)
    model_year = FuzzyChoice(choices=[2019, 2020, 2021, 2022, 2023])
    quantity = FuzzyChoice(choices=[0, 5, 10, 15, 20])
    brand = FuzzyChoice(
        choices=[
            Brand.UNKNOWN,
            Brand.TESLA,
            Brand.FORD,
            Brand.HONDA,
            Brand.TOYOTA,
            Brand.BMW,
        ]
    )
    category = FuzzyChoice(
        choices=[Category.UNKNOWN, Category.SUV, Category.SEDAN, Category.SPORTS]
    )
