import json
from typing import List, Dict, Any


DEMO_MEAL_PLAN = {
    "Monday": {
        "breakfast": "Oatmeal with berries and honey (V, DF option)",
        "lunch": "Vegetable minestrone soup with crusty bread",
        "dinner": "Lentil dal with basmati rice and soft naan (V, soft-food friendly)"
    },
    "Tuesday": {
        "breakfast": "Scrambled eggs with whole-wheat toast and fruit",
        "lunch": "Chicken Caesar salad (grilled chicken separate for Sarah)",
        "dinner": "Baked salmon with steamed broccoli and mashed potatoes"
    },
    "Wednesday": {
        "breakfast": "Greek yogurt parfait with granola and strawberries (V)",
        "lunch": "Caprese sandwich on soft focaccia (V)",
        "dinner": "Mushroom and spinach pasta with marinara sauce (V)"
    },
    "Thursday": {
        "breakfast": "Banana pancakes with maple syrup",
        "lunch": "Turkey and avocado wrap (soft tortilla for George)",
        "dinner": "Chicken stir-fry with mixed vegetables and jasmine rice"
    },
    "Friday": {
        "breakfast": "Smoothie bowls with mango and coconut (V, GF)",
        "lunch": "Tomato basil soup with grilled cheese on soft bread (V)",
        "dinner": "Baked cod with roasted sweet potatoes and green beans"
    },
    "Saturday": {
        "breakfast": "Vegetable omelette with whole grain toast (V)",
        "lunch": "Hummus and veggie platter with soft pita (V)",
        "dinner": "Eggplant parmesan with Caesar salad (V)"
    },
    "Sunday": {
        "breakfast": "French toast with fresh berries and light syrup",
        "lunch": "Butternut squash soup with soft dinner rolls",
        "dinner": "Roast chicken with soft roasted vegetables and gravy"
    }
}

ALLERGEN_MAP = {
    "peanuts": ["peanut", "peanut butter", "peanut oil", "groundnut"],
    "tree nuts": ["almond", "walnut", "cashew", "pecan", "pistachio", "hazelnut", "macadamia"],
    "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "whey", "casein"],
    "gluten": ["wheat", "bread", "pasta", "flour", "barley", "rye", "oat"],
    "shellfish": ["shrimp", "crab", "lobster", "clam", "oyster", "mussel", "scallop"],
    "eggs": ["egg", "eggs", "mayonnaise"],
    "soy": ["soy", "tofu", "tempeh", "edamame", "soy sauce"],
    "fish": ["salmon", "tuna", "cod", "tilapia", "halibut", "anchovy"],
}


def generate_meal_plan(household_members: List[Dict], preferences: Dict = None) -> Dict:
    """Generate a 7-day meal plan respecting household constraints."""
    restrictions = set()
    allergies = set()

    for member in household_members:
        for r in member.get("dietary_restrictions", []):
            restrictions.add(r.lower())
        for a in member.get("allergies", []):
            allergies.add(a.lower())

    # Return demo plan (in production, AI would generate dynamically)
    return {
        "plan": DEMO_MEAL_PLAN,
        "notes": f"Plan respects restrictions: {list(restrictions)}, avoids allergens: {list(allergies)}",
        "week_start": "2026-10-14"
    }


def check_ingredient_safety(ingredient: str, household_members: List[Dict]) -> Dict:
    """Check if an ingredient is safe for all household members."""
    ingredient_lower = ingredient.lower()
    conflicts = []

    for member in household_members:
        for allergy in member.get("allergies", []):
            allergy_lower = allergy.lower()
            trigger_words = ALLERGEN_MAP.get(allergy_lower, [allergy_lower])
            for trigger in trigger_words:
                if trigger in ingredient_lower:
                    conflicts.append({
                        "member": member["name"],
                        "allergy": allergy,
                        "ingredient": ingredient
                    })
                    break

        for restriction in member.get("dietary_restrictions", []):
            if restriction.lower() == "vegetarian":
                meat_words = ["chicken", "beef", "pork", "lamb", "turkey", "bacon", "ham", "sausage"]
                for meat in meat_words:
                    if meat in ingredient_lower:
                        conflicts.append({
                            "member": member["name"],
                            "restriction": restriction,
                            "ingredient": ingredient,
                            "note": "vegetarian cannot eat meat"
                        })
                        break

    return {
        "ingredient": ingredient,
        "safe": len(conflicts) == 0,
        "conflicts": conflicts,
        "recommendation": "Safe for all members" if not conflicts else f"Conflicts found: {len(conflicts)} member(s) affected"
    }


def calculate_servings(recipe: Dict, num_people: int) -> Dict:
    """Scale a recipe for the given number of people."""
    base_servings = recipe.get("servings", 4)
    scale_factor = num_people / base_servings

    scaled_ingredients = []
    for ingredient in recipe.get("ingredients", []):
        scaled = ingredient.copy()
        if "qty" in scaled and isinstance(scaled["qty"], (int, float)):
            scaled["qty"] = round(scaled["qty"] * scale_factor, 2)
        scaled_ingredients.append(scaled)

    return {
        "recipe_name": recipe.get("name", "Unknown Recipe"),
        "original_servings": base_servings,
        "target_servings": num_people,
        "scale_factor": round(scale_factor, 2),
        "scaled_ingredients": scaled_ingredients,
        "notes": f"Scaled from {base_servings} to {num_people} servings"
    }
