from pydantic import BaseModel, conlist, constr, Decimal
from typing import List

class MenuItem(BaseModel):
    brand: constr(strip_whitespace=True, min_length=1)  # Non-empty string that trims whitespace
    product: constr(strip_whitespace=True, min_length=1)  # Non-empty string that trims whitespace
    ingredients: List[constr(strip_whitespace=True, min_length=1)]  # List of non-empty strings
    price: float  # Changed from Decimal to float for simplicity
    size: constr(strip_whitespace=True, min_length=1)  # Description of size, e.g., '500ml', '1 pint'
    description: constr(strip_whitespace=True, min_length=1)  # Non-empty string

# Example usage
item_example = MenuItem(
    brand="Brand Name",
    product="Product Name",
    ingredients=["Ingredient 1", "Ingredient 2"],
    price=9.99,
    size="500ml",
    description="A refreshing cocktail with a blend of premium ingredients."
)

print(item_example)
