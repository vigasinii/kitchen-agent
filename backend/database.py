import json
from sqlmodel import SQLModel, create_engine, Session, select
from models import HouseholdMember, MealPlan, GroceryList

DATABASE_URL = "sqlite:///./kitchen_os.db"
engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session


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
        "dinner": "Roast chicken with soft roasted vegetables and gravy (Emma gets drumstick)"
    }
}


def init_db():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Seed household members if empty
        members = session.exec(select(HouseholdMember)).all()
        if not members:
            demo_members = [
                HouseholdMember(
                    name="Sarah",
                    dietary_restrictions=json.dumps(["vegetarian"]),
                    allergies=json.dumps([]),
                    preferences=json.dumps(["Mediterranean", "Indian", "salads"])
                ),
                HouseholdMember(
                    name="Mike",
                    dietary_restrictions=json.dumps([]),
                    allergies=json.dumps([]),
                    preferences=json.dumps(["grilled meats", "pasta", "BBQ"])
                ),
                HouseholdMember(
                    name="Emma",
                    dietary_restrictions=json.dumps(["kid-friendly"]),
                    allergies=json.dumps(["peanuts"]),
                    preferences=json.dumps(["mac and cheese", "pizza", "chicken nuggets", "mild flavors"])
                ),
                HouseholdMember(
                    name="George",
                    dietary_restrictions=json.dumps(["soft foods", "low spice", "diabetic-friendly"]),
                    allergies=json.dumps([]),
                    preferences=json.dumps(["soups", "stews", "well-cooked vegetables"])
                ),
            ]
            for m in demo_members:
                session.add(m)
            session.commit()

        # Seed demo meal plan if none exists
        plans = session.exec(select(MealPlan)).all()
        if not plans:
            plan = MealPlan(
                week_start="2026-10-14",
                status="approved",
                meals=json.dumps(DEMO_MEAL_PLAN)
            )
            session.add(plan)
            session.flush()

            # Generate grocery list
            from tools.grocery import consolidate_grocery_list
            items = consolidate_grocery_list(DEMO_MEAL_PLAN)
            grocery = GroceryList(
                meal_plan_id=plan.id,
                items=json.dumps(items),
                status="pending"
            )
            session.add(grocery)
            session.commit()
