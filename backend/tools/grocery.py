import json
import random
import string
from typing import List, Dict, Any


INGREDIENT_DATABASE = {
    "oatmeal": {"unit": "cups", "qty_per_serving": 0.5, "category": "grains"},
    "berries": {"unit": "cups", "qty_per_serving": 0.5, "category": "produce"},
    "honey": {"unit": "tbsp", "qty_per_serving": 1, "category": "pantry"},
    "eggs": {"unit": "count", "qty_per_serving": 2, "category": "dairy/eggs"},
    "bread": {"unit": "loaves", "qty_per_serving": 0.1, "category": "bakery"},
    "chicken": {"unit": "lbs", "qty_per_serving": 0.5, "category": "meat"},
    "salmon": {"unit": "lbs", "qty_per_serving": 0.4, "category": "seafood"},
    "pasta": {"unit": "lbs", "qty_per_serving": 0.25, "category": "grains"},
    "rice": {"unit": "cups", "qty_per_serving": 0.5, "category": "grains"},
    "lentils": {"unit": "cups", "qty_per_serving": 0.5, "category": "legumes"},
    "mushrooms": {"unit": "lbs", "qty_per_serving": 0.25, "category": "produce"},
    "spinach": {"unit": "bags", "qty_per_serving": 0.2, "category": "produce"},
    "tomatoes": {"unit": "count", "qty_per_serving": 1, "category": "produce"},
    "broccoli": {"unit": "heads", "qty_per_serving": 0.25, "category": "produce"},
    "potatoes": {"unit": "lbs", "qty_per_serving": 0.5, "category": "produce"},
    "sweet potatoes": {"unit": "lbs", "qty_per_serving": 0.5, "category": "produce"},
    "avocado": {"unit": "count", "qty_per_serving": 0.5, "category": "produce"},
    "eggplant": {"unit": "count", "qty_per_serving": 0.5, "category": "produce"},
    "butternut squash": {"unit": "count", "qty_per_serving": 0.25, "category": "produce"},
    "cod": {"unit": "lbs", "qty_per_serving": 0.4, "category": "seafood"},
    "turkey": {"unit": "lbs", "qty_per_serving": 0.4, "category": "meat"},
    "whole chicken": {"unit": "count", "qty_per_serving": 0.25, "category": "meat"},
    "yogurt": {"unit": "cups", "qty_per_serving": 0.5, "category": "dairy/eggs"},
    "milk": {"unit": "gallons", "qty_per_serving": 0.1, "category": "dairy/eggs"},
    "butter": {"unit": "sticks", "qty_per_serving": 0.2, "category": "dairy/eggs"},
    "cheese": {"unit": "lbs", "qty_per_serving": 0.15, "category": "dairy/eggs"},
    "mozzarella": {"unit": "lbs", "qty_per_serving": 0.2, "category": "dairy/eggs"},
    "olive oil": {"unit": "bottles", "qty_per_serving": 0.05, "category": "pantry"},
    "garlic": {"unit": "heads", "qty_per_serving": 0.2, "category": "produce"},
    "onion": {"unit": "count", "qty_per_serving": 0.5, "category": "produce"},
    "marinara sauce": {"unit": "jars", "qty_per_serving": 0.25, "category": "pantry"},
    "pita bread": {"unit": "packages", "qty_per_serving": 0.5, "category": "bakery"},
    "hummus": {"unit": "containers", "qty_per_serving": 0.25, "category": "deli"},
    "granola": {"unit": "boxes", "qty_per_serving": 0.15, "category": "cereal"},
    "mango": {"unit": "count", "qty_per_serving": 0.5, "category": "produce"},
    "coconut milk": {"unit": "cans", "qty_per_serving": 0.25, "category": "pantry"},
    "bananas": {"unit": "count", "qty_per_serving": 1, "category": "produce"},
    "maple syrup": {"unit": "bottles", "qty_per_serving": 0.05, "category": "pantry"},
    "green beans": {"unit": "lbs", "qty_per_serving": 0.25, "category": "produce"},
    "naan": {"unit": "packages", "qty_per_serving": 0.5, "category": "bakery"},
    "focaccia": {"unit": "loaves", "qty_per_serving": 0.25, "category": "bakery"},
    "dinner rolls": {"unit": "packages", "qty_per_serving": 0.5, "category": "bakery"},
    "caesar dressing": {"unit": "bottles", "qty_per_serving": 0.1, "category": "pantry"},
    "parmesan": {"unit": "bags", "qty_per_serving": 0.1, "category": "dairy/eggs"},
}

MEAL_INGREDIENTS = {
    "Oatmeal with berries and honey": ["oatmeal", "berries", "honey", "milk"],
    "Vegetable minestrone soup": ["tomatoes", "onion", "garlic", "pasta", "olive oil"],
    "Lentil dal with basmati rice": ["lentils", "rice", "onion", "garlic", "olive oil", "naan"],
    "Scrambled eggs with whole-wheat toast": ["eggs", "butter", "bread"],
    "Chicken Caesar salad": ["chicken", "caesar dressing", "parmesan"],
    "Baked salmon with steamed broccoli": ["salmon", "broccoli", "potatoes", "butter"],
    "Greek yogurt parfait": ["yogurt", "granola", "berries"],
    "Caprese sandwich on soft focaccia": ["mozzarella", "tomatoes", "focaccia", "olive oil"],
    "Mushroom and spinach pasta": ["mushrooms", "spinach", "pasta", "marinara sauce", "parmesan"],
    "Banana pancakes": ["bananas", "eggs", "milk", "butter", "maple syrup"],
    "Turkey and avocado wrap": ["turkey", "avocado", "bread"],
    "Chicken stir-fry": ["chicken", "rice", "garlic", "onion", "olive oil"],
    "Smoothie bowls": ["mango", "coconut milk", "berries"],
    "Tomato basil soup with grilled cheese": ["tomatoes", "garlic", "bread", "butter", "cheese"],
    "Baked cod with roasted sweet potatoes": ["cod", "sweet potatoes", "green beans", "olive oil"],
    "Vegetable omelette": ["eggs", "spinach", "mushrooms", "butter", "bread"],
    "Hummus and veggie platter": ["hummus", "pita bread", "tomatoes", "garlic"],
    "Eggplant parmesan": ["eggplant", "marinara sauce", "mozzarella", "parmesan"],
    "French toast": ["eggs", "bread", "butter", "berries", "maple syrup"],
    "Butternut squash soup": ["butternut squash", "onion", "garlic", "olive oil", "dinner rolls"],
    "Roast chicken": ["whole chicken", "potatoes", "onion", "garlic", "olive oil", "butter"],
}


def consolidate_grocery_list(meal_plan: Dict) -> List[Dict]:
    """Merge all ingredients from a 7-day plan into unified shopping list."""
    ingredient_totals = {}

    for day, meals in meal_plan.items():
        for meal_type, meal_name in meals.items():
            # Find matching ingredients
            matched_ingredients = []
            for key, ingredients in MEAL_INGREDIENTS.items():
                if key.lower() in meal_name.lower() or meal_name.lower() in key.lower():
                    matched_ingredients = ingredients
                    break
            if not matched_ingredients:
                # Try partial match on first word
                for key, ingredients in MEAL_INGREDIENTS.items():
                    first_word = meal_name.split()[0].lower()
                    if first_word in key.lower():
                        matched_ingredients = ingredients
                        break

            for ingredient in matched_ingredients:
                if ingredient in INGREDIENT_DATABASE:
                    info = INGREDIENT_DATABASE[ingredient]
                    if ingredient not in ingredient_totals:
                        ingredient_totals[ingredient] = {
                            "name": ingredient.title(),
                            "qty": 0,
                            "unit": info["unit"],
                            "category": info["category"]
                        }
                    ingredient_totals[ingredient]["qty"] += info["qty_per_serving"] * 4  # 4 people

    # Round quantities
    result = []
    for name, item in ingredient_totals.items():
        item = item.copy()
        item["qty"] = round(item["qty"], 1)
        result.append(item)

    # Sort by category
    result.sort(key=lambda x: (x["category"], x["name"]))
    return result


def simulate_instamart_order(grocery_list: List[Dict]) -> Dict:
    """Simulate placing a grocery order. Returns fake order details."""
    order_id = "IM-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    item_count = len(grocery_list)

    # Simulate cost (rough estimate)
    base_cost = 0
    price_map = {"grains": 3, "produce": 4, "meat": 12, "seafood": 14, "dairy/eggs": 5,
                 "pantry": 6, "bakery": 4, "legumes": 3, "deli": 5, "cereal": 6}
    for item in grocery_list:
        cat = item.get("category", "pantry")
        base_cost += price_map.get(cat, 5) * max(1, item.get("qty", 1))

    total_cost = round(base_cost, 2)
    delivery_minutes = random.randint(45, 90)

    return {
        "success": True,
        "order_id": order_id,
        "item_count": item_count,
        "total_cost": f"${total_cost:.2f}",
        "estimated_delivery": f"{delivery_minutes} minutes",
        "status": "Order placed successfully",
        "message": f"Your {item_count} items have been ordered! Order #{order_id} will arrive in approximately {delivery_minutes} minutes. Total: ${total_cost:.2f}"
    }
