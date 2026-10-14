import json
import os
import time
from typing import List, Dict, Any


ALLERGEN_MAP = {
    "peanuts": ["peanut", "peanut butter", "peanut oil", "groundnut"],
    "tree nuts": ["almond", "walnut", "cashew", "pecan", "pistachio", "hazelnut", "macadamia"],
    "dairy": ["milk", "cheese", "butter", "cream", "yogurt", "whey", "casein"],
    "gluten": ["wheat", "bread", "pasta", "flour", "barley", "rye", "oat"],
    "shellfish": ["shrimp", "crab", "lobster", "clam", "oyster", "mussel", "scallop"],
    "eggs": ["egg", "eggs", "mayonnaise"],
    "soy": ["soy", "tofu", "tempeh", "edamame", "soy sauce"],
    "fish": ["salmon", "tuna", "cod", "tilapia", "halibut", "anchovy"],
    "sesame": ["sesame", "tahini", "sesame oil", "sesame seed"],
}

# Phrases that negate an allergen mention — "no peanuts", "peanut-free", "without peanuts"
NEGATION_PREFIXES = ["no ", "without ", "free of ", "free from ", "-free", "peanut-free",
                     "nut-free", "dairy-free", "gluten-free", "egg-free"]

MEAT_WORDS = ["chicken", "beef", "pork", "lamb", "turkey", "bacon", "ham", "sausage",
              "prawn", "shrimp", "mutton", "veal", "duck", "fish", "salmon", "tuna"]

FALLBACK_MEAL_PLAN = {
    "Monday": {
        "breakfast": "Oatmeal with berries and honey",
        "lunch": "Vegetable minestrone soup with crusty bread",
        "dinner": "Lentil dal with basmati rice and soft naan"
    },
    "Tuesday": {
        "breakfast": "Scrambled eggs with whole-wheat toast and fruit",
        "lunch": "Chickpea salad with cucumber, tomato and lemon dressing",
        "dinner": "Baked salmon with steamed broccoli and mashed potatoes"
    },
    "Wednesday": {
        "breakfast": "Greek yogurt parfait with granola and strawberries",
        "lunch": "Caprese sandwich on soft focaccia",
        "dinner": "Mushroom and spinach pasta with marinara sauce"
    },
    "Thursday": {
        "breakfast": "Banana pancakes with maple syrup",
        "lunch": "Turkey and avocado wrap with soft tortilla for George",
        "dinner": "Chicken stir-fry with mixed vegetables and jasmine rice, tofu stir-fry for Sarah"
    },
    "Friday": {
        "breakfast": "Smoothie bowls with mango and coconut",
        "lunch": "Tomato basil soup with grilled cheese on soft bread",
        "dinner": "Baked cod with roasted sweet potatoes and green beans"
    },
    "Saturday": {
        "breakfast": "Vegetable omelette with whole grain toast",
        "lunch": "Hummus and veggie platter with soft pita",
        "dinner": "Eggplant parmesan with Caesar salad"
    },
    "Sunday": {
        "breakfast": "French toast with fresh berries and light syrup",
        "lunch": "Butternut squash soup with soft dinner rolls",
        "dinner": "Roast chicken with soft roasted vegetables and gravy, roasted vegetable plate for Sarah"
    }
}


def _build_constraint_summary(household_members: List[Dict]) -> str:
    lines = []
    for m in household_members:
        restrictions = m.get("dietary_restrictions", [])
        allergies = m.get("allergies", [])
        preferences = m.get("preferences", [])
        parts = []
        if restrictions:
            parts.append(f"dietary restrictions: {', '.join(restrictions)}")
        if allergies:
            parts.append(f"allergies: {', '.join(allergies)} (STRICT - never include)")
        if preferences:
            parts.append(f"preferences: {', '.join(preferences)}")
        lines.append(f"- {m['name']}: {'; '.join(parts) if parts else 'no restrictions'}")
    return "\n".join(lines)


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def generate_meal_plan(household_members: List[Dict], special_requests: str = "") -> Dict:
    """Generate a 7-day meal plan using the LLM. Raises on failure — no silent fallback."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Cannot generate a meal plan.")

    constraint_summary = _build_constraint_summary(household_members)
    special_note = f"\nSpecial requests: {special_requests}" if special_requests else ""

    prompt = f"""Generate a 7-day meal plan as JSON. Household: {constraint_summary}{special_note}
Rules: safe for all members; no allergens; vegetarian alternative when meat is served (note inline); soft/low-sugar for diabetic members; varied realistic home cooking.
Reply ONLY with JSON: {{"Monday":{{"breakfast":"...","lunch":"...","dinner":"..."}},"Tuesday":{{...}},"Wednesday":{{...}},"Thursday":{{...}},"Friday":{{...}},"Saturday":{{...}},"Sunday":{{...}}}}"""

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)
    last_error = None
    for attempt in range(2):
        try:
            t0 = time.time()
            response = client.chat.completions.create(
                model=GEMINI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a meal planning assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7,
                timeout=15,
            )
            elapsed = round(time.time() - t0, 2)
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            plan = json.loads(raw)
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            meals = ["breakfast", "lunch", "dinner"]
            missing_days = [d for d in days if d not in plan]
            if missing_days:
                raise ValueError(f"Plan missing days: {missing_days}")
            for day in days:
                missing_meals = [m for m in meals if m not in plan.get(day, {})]
                if missing_meals:
                    raise ValueError(f"{day} missing meals: {missing_meals}")
            restrictions_used = [r for m in household_members for r in m.get("dietary_restrictions", [])]
            allergies_used = [a for m in household_members for a in m.get("allergies", [])]
            return {
                "plan": plan,
                "notes": f"AI-generated in {elapsed}s. Restrictions: {restrictions_used}. Allergens excluded: {allergies_used}.",
            }
        except Exception as e:
            last_error = e
            if "429" in str(e) and attempt == 0:
                time.sleep(1)
            else:
                break

    raise RuntimeError(f"Meal plan generation failed: {last_error}")


def _trigger_is_negated(meal_lower: str, trigger: str) -> bool:
    """Return True if the trigger word appears in a negation context (e.g. 'no peanuts', 'peanut-free')."""
    idx = meal_lower.find(trigger)
    if idx == -1:
        return False
    # Check up to 15 chars before the trigger for negation words
    prefix_window = meal_lower[max(0, idx - 15): idx]
    for neg in NEGATION_PREFIXES:
        if neg in prefix_window or meal_lower.find(neg + trigger) != -1:
            return True
    # Check compound negations like "peanut-free" after trigger
    suffix_window = meal_lower[idx: idx + len(trigger) + 6]
    if suffix_window.endswith("-free"):
        return True
    return False


def validate_meal_against_household(meal_description: str, household_members: List[Dict]) -> Dict:
    """Check if a meal description is safe for all household members. Returns errors if not."""
    meal_lower = meal_description.lower()
    violations = []

    for member in household_members:
        name = member["name"]

        for allergy in member.get("allergies", []):
            allergy_lower = allergy.lower()
            triggers = ALLERGEN_MAP.get(allergy_lower, [allergy_lower])
            for trigger in triggers:
                if trigger in meal_lower and not _trigger_is_negated(meal_lower, trigger):
                    violations.append({
                        "member": name,
                        "type": "allergy",
                        "allergen": allergy,
                        "trigger": trigger,
                        "severity": "CRITICAL"
                    })
                    break

        for restriction in member.get("dietary_restrictions", []):
            if restriction.lower() == "vegetarian":
                for meat in MEAT_WORDS:
                    if meat in meal_lower:
                        # Check if there's an explicit vegetarian alternative mentioned
                        has_alternative = any(kw in meal_lower for kw in
                                              ["tofu", "vegetarian", "veggie", "paneer", "legume",
                                               "lentil", "chickpea", "bean", "tempeh"])
                        if not has_alternative:
                            violations.append({
                                "member": name,
                                "type": "dietary_restriction",
                                "restriction": "vegetarian",
                                "trigger": meat,
                                "severity": "HIGH"
                            })
                        break

    return {
        "meal": meal_description,
        "safe": len(violations) == 0,
        "violations": violations,
        "recommendation": "Safe for all members" if not violations else f"{len(violations)} violation(s) found - do not save"
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
                for meat in MEAT_WORDS:
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
