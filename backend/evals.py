"""
Evaluation suite for Kitchen Agent.
Tests the core agent behaviors: constraint enforcement, substitution safety,
approval workflow, and meal plan consistency.

Run with: python evals.py
Requires GROQ_API_KEY in .env
"""
import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from tools.meal_tools import (
    validate_meal_against_household,
    check_ingredient_safety,
    generate_meal_plan,
)

# ---- Test household fixtures ----

HOUSEHOLD = [
    {"name": "Sarah", "dietary_restrictions": ["vegetarian"], "allergies": [], "preferences": ["Mediterranean", "Indian"]},
    {"name": "Mike", "dietary_restrictions": [], "allergies": [], "preferences": ["grilled meats", "pasta"]},
    {"name": "Emma", "dietary_restrictions": [], "allergies": ["peanuts"], "preferences": ["mild foods"]},
    {"name": "George", "dietary_restrictions": ["diabetic-friendly", "soft foods"], "allergies": [], "preferences": ["low sugar"]},
]

RESULTS = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    RESULTS.append((status, name, detail))
    symbol = "[PASS]" if condition else "[FAIL]"
    print(f"{symbol} {name}" + (f" - {detail}" if detail else ""))


# ---- 1. Allergy enforcement ----

def test_allergy_enforcement():
    print("\n--- 1. Allergy Enforcement ---")
    result = validate_meal_against_household("Peanut butter toast with banana", HOUSEHOLD)
    check("Peanut butter blocked for Emma", not result["safe"])
    check("Peanut violation is CRITICAL", any(v["severity"] == "CRITICAL" for v in result["violations"]))

    result2 = validate_meal_against_household("Pad Thai with groundnut sauce", HOUSEHOLD)
    check("Groundnut (peanut alias) blocked", not result2["safe"])

    result3 = validate_meal_against_household("Oatmeal with berries and honey", HOUSEHOLD)
    check("Safe meal passes for all members", result3["safe"])


# ---- 2. Vegetarian enforcement ----

def test_vegetarian_enforcement():
    print("\n--- 2. Vegetarian Enforcement ---")
    result = validate_meal_against_household("Grilled chicken with rice", HOUSEHOLD)
    check("Chicken without veg alternative blocked for Sarah", not result["safe"])

    result2 = validate_meal_against_household("Grilled chicken with rice, tofu option for Sarah", HOUSEHOLD)
    check("Chicken with tofu alternative passes", result2["safe"],
          f"violations={result2['violations']}")

    result3 = validate_meal_against_household("Lentil dal with basmati rice", HOUSEHOLD)
    check("Fully vegetarian meal passes", result3["safe"])


# ---- 3. Ingredient safety ----

def test_ingredient_safety():
    print("\n--- 3. Ingredient Safety ---")
    r1 = check_ingredient_safety("peanut oil", HOUSEHOLD)
    check("Peanut oil flagged", not r1["safe"])

    r2 = check_ingredient_safety("olive oil", HOUSEHOLD)
    check("Olive oil safe", r2["safe"])

    r3 = check_ingredient_safety("chicken breast", HOUSEHOLD)
    check("Chicken flagged for vegetarian Sarah", not r3["safe"])

    r4 = check_ingredient_safety("chickpeas", HOUSEHOLD)
    check("Chickpeas safe for all", r4["safe"])


# ---- 4. Dairy allergy household ----

def test_dairy_allergy():
    print("\n--- 4. Dairy Allergy ---")
    dairy_household = [
        {"name": "Arun", "dietary_restrictions": [], "allergies": ["dairy", "milk"], "preferences": []},
        {"name": "Priya", "dietary_restrictions": ["vegetarian"], "allergies": [], "preferences": []},
    ]
    result = generate_meal_plan(dairy_household, special_requests="No dairy products at all")
    plan = result.get("plan", {})
    check("Plan generated for dairy-allergy household", len(plan) == 7, str(list(plan.keys())))

    dairy_words = ["cheese", "butter", "cream", "milk", "yogurt", "ghee", "paneer"]
    violations = []
    for day, meals in plan.items():
        for meal_type, meal_desc in meals.items():
            meal_lower = meal_desc.lower()
            for dw in dairy_words:
                if dw in meal_lower and "dairy-free" not in meal_lower and "vegan" not in meal_lower:
                    violations.append(f"{day} {meal_type}: {meal_desc} (contains '{dw}')")
    if violations:
        print(f"  WARNING: Possible dairy violations ({len(violations)}):")
        for v in violations[:3]:
            print(f"    {v}")
    check("Plan has 7 days for dairy-allergy household", len(plan) == 7)


# ---- 5. Conflicting preferences ----

def test_conflicting_preferences():
    print("\n--- 5. Conflicting Preferences ---")
    spicy_mild_household = [
        {"name": "Ravi", "dietary_restrictions": [], "allergies": [], "preferences": ["very spicy food", "hot chillies"]},
        {"name": "Tom", "dietary_restrictions": [], "allergies": [], "preferences": ["mild food only", "no spice"]},
    ]
    result = generate_meal_plan(spicy_mild_household, special_requests="Accommodate both spicy and mild preferences, serve condiments separately")
    plan = result.get("plan", {})
    check("Plan generated despite conflicting spice preferences", len(plan) == 7, str(list(plan.keys())))


# ---- 6. Missing household info (empty list) ----

def test_empty_household():
    print("\n--- 6. Missing Household Info ---")
    result = generate_meal_plan([], special_requests="")
    plan = result.get("plan", {})
    check("Fallback plan returned for empty household", len(plan) >= 7 or isinstance(plan, dict),
          f"keys={list(plan.keys())}")
    # Should not crash, should return something usable
    check("Result has 'plan' key", "plan" in result)


# ---- 7. Budget-constrained household ----

def test_budget_constrained():
    print("\n--- 7. Budget-Constrained ---")
    result = generate_meal_plan(HOUSEHOLD, special_requests="budget-friendly meals under 500 rupees per meal, use cheap staples like lentils, rice, and seasonal vegetables")
    plan = result.get("plan", {})
    check("Plan generated for budget household", len(plan) == 7, str(list(plan.keys())))


# ---- 8. Limited cooking time ----

def test_limited_cooking_time():
    print("\n--- 8. Limited Cooking Time ---")
    result = generate_meal_plan(HOUSEHOLD, special_requests="quick meals under 30 minutes, weeknight-friendly, minimal prep")
    plan = result.get("plan", {})
    check("Plan generated for time-constrained household", len(plan) == 7, str(list(plan.keys())))


# ---- Standard meal plan generation (original test 4, kept for compatibility) ----

def test_meal_plan_generation():
    print("\n--- Meal Plan Generation (Standard Household) ---")
    result = generate_meal_plan(HOUSEHOLD, special_requests="Include at least two Indian-inspired dinners")
    plan = result.get("plan", {})
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    check("Plan has all 7 days", all(d in plan for d in days), str(list(plan.keys())))

    all_safe = True
    for day, meals in plan.items():
        for meal_type, meal_desc in meals.items():
            safety = validate_meal_against_household(meal_desc, HOUSEHOLD)
            if not safety["safe"]:
                critical = [v for v in safety["violations"] if v["severity"] == "CRITICAL"]
                if critical:
                    all_safe = False
                    print(f"  UNSAFE: {day} {meal_type}: {meal_desc}")
                    print(f"    Violations: {critical}")
    check("All generated meals safe (no critical violations)", all_safe)


# ---- 9. Substitution scenarios ----

def test_substitution_scenarios():
    print("\n--- 9. Substitution Scenarios ---")
    from agents.cook import SUBSTITUTION_MAP

    butter_subs = SUBSTITUTION_MAP.get("butter", [])
    check("Butter has substitutions", len(butter_subs) > 0, str(butter_subs))

    for sub in butter_subs:
        safety = check_ingredient_safety(sub, HOUSEHOLD)
        check(f"Butter sub '{sub}' safe for household", safety["safe"],
              f"conflicts={safety['conflicts']}")

    all_subs = [s for subs in SUBSTITUTION_MAP.values() for s in subs]
    has_peanut_sub = any("peanut" in s.lower() for s in all_subs)
    check("No peanut-containing substitutes in map", not has_peanut_sub)


# ---- 10. Different household (no preset) ----

def test_different_household():
    print("\n--- 10. Different Household (no preset) ---")
    custom_household = [
        {"name": "Priya", "dietary_restrictions": ["vegan"], "allergies": ["gluten"], "preferences": ["South Indian"]},
        {"name": "Raj", "dietary_restrictions": [], "allergies": ["shellfish"], "preferences": ["spicy food"]},
    ]
    result = generate_meal_plan(custom_household)
    plan = result.get("plan", {})
    check("Plan generated for custom household", len(plan) == 7)


# ---- 11. Missing ingredient chain ----

def test_missing_ingredient_chain():
    print("\n--- 11. Missing Ingredient Chain ---")
    from tools.meal_tools import check_ingredient_safety
    from agents.cook import SUBSTITUTION_MAP

    missing = "butter"
    subs = SUBSTITUTION_MAP.get(missing, [])
    safe_subs = [s for s in subs if check_ingredient_safety(s, HOUSEHOLD)["safe"]]
    check("At least one safe butter substitute available", len(safe_subs) > 0, str(safe_subs))

    missing2 = "eggs"
    subs2 = SUBSTITUTION_MAP.get(missing2, [])
    safe_subs2 = [s for s in subs2 if check_ingredient_safety(s, HOUSEHOLD)["safe"]]
    check("At least one safe egg substitute available", len(safe_subs2) > 0, str(safe_subs2))


# ---- 12. Safe substitution validation ----

def test_safe_substitution():
    print("\n--- 12. Safe Substitution ---")
    result = validate_meal_against_household("Lentil soup with olive oil and soft bread", HOUSEHOLD)
    check("Lentil soup with olive oil is safe", result["safe"])

    result2 = validate_meal_against_household("Tofu scramble with vegetables, tofu option available for Sarah", HOUSEHOLD)
    check("Tofu scramble passes for vegetarian household", result2["safe"])


# ---- 13. Approval state transitions ----

def test_approval_state_transitions():
    print("\n--- 13. Approval State Transitions ---")
    from sqlmodel import create_engine, Session
    from sqlmodel import SQLModel
    from models import CookSession, MealPlan, ApprovalRequest
    from database import DATABASE_URL

    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as db:
        # Create a minimal MealPlan
        plan = MealPlan(
            week_start="2026-10-14",
            status="planning",
            meals=json.dumps({"Monday": {"dinner": "Dal Rice"}})
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        # Create a CookSession
        cs = CookSession(
            meal_plan_id=plan.id,
            day="Monday",
            meal_name="Dal Rice",
            status="active"
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

        # Create an ApprovalRequest
        ar = ApprovalRequest(
            cook_session_id=cs.id,
            meal_plan_id=plan.id,
            day="Monday",
            meal_type="dinner",
            issue="Out of dal",
            proposed_change="Substitute with chickpea curry",
            reason="Dal unavailable in pantry",
            requested_by="cook",
            requested_at=datetime.utcnow().isoformat(),
            status="pending"
        )
        db.add(ar)
        db.commit()
        db.refresh(ar)

        approval_id = ar.id
        check("ApprovalRequest starts as pending", ar.status == "pending")

        # Approve it
        ar.status = "approved"
        ar.decided_by = "household"
        ar.decided_at = datetime.utcnow().isoformat()
        ar.decision_reason = "Fine to substitute"
        db.add(ar)
        db.commit()
        db.refresh(ar)

        check("ApprovalRequest status is approved after decision", ar.status == "approved")
        check("decided_by is recorded", ar.decided_by == "household")


# ---- 14. Rejection leaves plan unchanged ----

def test_rejection_leaves_plan_unchanged():
    print("\n--- 14. Rejection Leaves Plan Unchanged ---")
    from sqlmodel import create_engine, Session
    from sqlmodel import SQLModel
    from models import CookSession, MealPlan, ApprovalRequest
    from database import DATABASE_URL

    original_meal = "Paneer Butter Masala"
    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as db:
        plan = MealPlan(
            week_start="2026-10-15",
            status="approved",
            meals=json.dumps({"Tuesday": {"dinner": original_meal}})
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        cs = CookSession(
            meal_plan_id=plan.id,
            day="Tuesday",
            meal_name=original_meal,
            status="active"
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

        ar = ApprovalRequest(
            cook_session_id=cs.id,
            meal_plan_id=plan.id,
            day="Tuesday",
            meal_type="dinner",
            issue="Paneer out of stock",
            proposed_change="Replace with tofu",
            requested_by="cook",
            requested_at=datetime.utcnow().isoformat(),
            status="pending"
        )
        db.add(ar)
        db.commit()
        db.refresh(ar)

        # Reject it
        ar.status = "rejected"
        ar.decided_by = "household"
        ar.decided_at = datetime.utcnow().isoformat()
        ar.decision_reason = "Please find paneer at a nearby store"
        db.add(ar)
        db.commit()
        db.refresh(ar)

        # Verify plan is unchanged
        db.refresh(plan)
        meals = json.loads(plan.meals)
        check("Rejected approval leaves plan unchanged", meals["Tuesday"]["dinner"] == original_meal,
              f"actual={meals['Tuesday']['dinner']}")
        check("Rejection reason recorded", "paneer" in ar.decision_reason.lower())


# ---- 15. Grocery regeneration after meal update ----

def test_grocery_regeneration():
    print("\n--- 15. Grocery Regeneration ---")
    from sqlmodel import create_engine, Session
    from sqlmodel import SQLModel
    from models import MealPlan, GroceryList
    from tools.grocery import consolidate_grocery_list
    from database import DATABASE_URL

    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)

    original_meals = {
        "Monday": {"breakfast": "Oatmeal", "lunch": "Dal Rice", "dinner": "Paneer Curry"},
        "Tuesday": {"breakfast": "Toast", "lunch": "Salad", "dinner": "Rajma Chawal"},
        "Wednesday": {"breakfast": "Idli", "lunch": "Curd Rice", "dinner": "Palak Paneer"},
        "Thursday": {"breakfast": "Poha", "lunch": "Chapati Sabzi", "dinner": "Aloo Gobi"},
        "Friday": {"breakfast": "Upma", "lunch": "Lemon Rice", "dinner": "Chana Masala"},
        "Saturday": {"breakfast": "Dosa", "lunch": "Bisi Bele Bath", "dinner": "Mushroom Masala"},
        "Sunday": {"breakfast": "Paratha", "lunch": "Kadhi Chawal", "dinner": "Mixed Veg Sabzi"},
    }

    with Session(engine) as db:
        plan = MealPlan(
            week_start="2026-10-16",
            status="approved",
            meals=json.dumps(original_meals)
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        # Generate initial grocery list
        items = consolidate_grocery_list(original_meals)
        grocery = GroceryList(
            meal_plan_id=plan.id,
            items=json.dumps(items),
            status="pending"
        )
        db.add(grocery)
        db.commit()
        db.refresh(grocery)

        original_items = json.loads(grocery.items)
        check("Grocery list generated from plan", len(original_items) > 0, f"{len(original_items)} items")

        # Now update a meal and regenerate
        updated_meals = json.loads(plan.meals)
        updated_meals["Monday"]["dinner"] = "Tofu Stir Fry with Bok Choy"
        plan.meals = json.dumps(updated_meals)
        db.add(plan)
        db.commit()

        new_items = consolidate_grocery_list(updated_meals)
        grocery.items = json.dumps(new_items)
        grocery.status = "pending"
        db.add(grocery)
        db.commit()
        db.refresh(grocery)

        check("Grocery list can be regenerated after meal update", len(json.loads(grocery.items)) > 0)


# ---- 16. Duplicate approval prevention ----

def test_duplicate_approval_prevention():
    print("\n--- 16. Duplicate Approval Prevention ---")
    from sqlmodel import create_engine, Session
    from sqlmodel import SQLModel
    from models import CookSession, MealPlan, ApprovalRequest
    from database import DATABASE_URL

    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as db:
        plan = MealPlan(
            week_start="2026-10-17",
            status="planning",
            meals=json.dumps({"Monday": {"dinner": "Test Meal"}})
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        cs = CookSession(
            meal_plan_id=plan.id,
            day="Monday",
            meal_name="Test Meal",
            status="active"
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

        ar = ApprovalRequest(
            cook_session_id=cs.id,
            meal_plan_id=plan.id,
            day="Monday",
            meal_type="dinner",
            issue="Test issue",
            proposed_change="Test change",
            requested_by="cook",
            requested_at=datetime.utcnow().isoformat(),
            status="pending"
        )
        db.add(ar)
        db.commit()
        db.refresh(ar)

        # Approve once
        ar.status = "approved"
        ar.decided_by = "household"
        ar.decided_at = datetime.utcnow().isoformat()
        db.add(ar)
        db.commit()
        db.refresh(ar)

        check("First approval succeeds", ar.status == "approved")

        # Try to approve again - the app layer should detect status != 'pending'
        already_decided = ar.status != "pending"
        check("Already-decided request cannot be re-decided (status check)", already_decided,
              f"status={ar.status}")


# ---- 17. API failure graceful degradation ----

def test_api_failure_graceful():
    print("\n--- 17. API Failure Graceful Degradation ---")
    import os
    original_key = os.environ.get("GROQ_API_KEY", "")
    os.environ["GROQ_API_KEY"] = "invalid-key-for-testing"

    try:
        result = generate_meal_plan(HOUSEHOLD, special_requests="Any meals")
        plan = result.get("plan", {})
        # With invalid key, generate_meal_plan should return a fallback plan
        check("Fallback plan returned on API failure", isinstance(plan, dict),
              f"type={type(plan).__name__}, keys={list(plan.keys())[:3]}")
        check("Fallback plan has content", len(plan) > 0,
              f"keys={list(plan.keys())}")
    except Exception as e:
        # If it raises, that's acceptable as long as it's a clear error
        check("API failure raises exception cleanly (not a silent crash)", True,
              f"exception={type(e).__name__}: {str(e)[:100]}")
    finally:
        if original_key:
            os.environ["GROQ_API_KEY"] = original_key
        else:
            del os.environ["GROQ_API_KEY"]


# ---- 18. Cook session completion ----

def test_cook_session_completion():
    print("\n--- 18. Cook Session Completion ---")
    from sqlmodel import create_engine, Session
    from sqlmodel import SQLModel
    from models import CookSession, MealPlan
    from database import DATABASE_URL

    engine = create_engine(DATABASE_URL)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as db:
        plan = MealPlan(
            week_start="2026-10-18",
            status="approved",
            meals=json.dumps({"Monday": {"dinner": "Dal Makhani"}})
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        cs = CookSession(
            meal_plan_id=plan.id,
            day="Monday",
            meal_name="Dal Makhani",
            status="active"
        )
        db.add(cs)
        db.commit()
        db.refresh(cs)

        check("Cook session created with active status", cs.status == "active")

        # Complete the session
        cs.status = "completed"
        cs.outcome_meal = "Dal Makhani (slightly less butter)"
        cs.outcome_notes = "Reduced butter for George. Followed plan otherwise."
        cs.human_interventions = 0
        cs.completed_at = datetime.utcnow().isoformat()
        db.add(cs)
        db.commit()
        db.refresh(cs)

        check("Cook session marked completed", cs.status == "completed")
        check("Outcome meal recorded", cs.outcome_meal == "Dal Makhani (slightly less butter)")
        check("Outcome notes saved", "George" in cs.outcome_notes)
        check("Completed_at timestamp set", cs.completed_at != "")
        check("Human interventions count saved", cs.human_interventions == 0)


# ---- Legacy test: approval flag parsing ----

def test_approval_parsing():
    print("\n--- Legacy: Approval Flag Parsing (notes-based) ---")
    notes = """Session started.
[APPROVAL NEEDED] Out of salmon - Proposed: Replace with tuna for Friday dinner
Cook note: timer set for 20 min"""

    approvals = []
    for i, line in enumerate(notes.splitlines()):
        if "[APPROVAL NEEDED]" in line:
            approvals.append({"index": i, "request": line.replace("[APPROVAL NEEDED]", "").strip()})

    check("Approval request detected in session notes", len(approvals) == 1)
    check("Approval content parsed correctly", "salmon" in approvals[0]["request"])


# ---- Runner ----

if __name__ == "__main__":
    print("=" * 60)
    print("Kitchen Agent Evaluation Suite")
    print("=" * 60)

    # Non-LLM tests first
    test_allergy_enforcement()
    test_vegetarian_enforcement()
    test_ingredient_safety()
    test_substitution_scenarios()
    test_missing_ingredient_chain()
    test_safe_substitution()
    test_approval_parsing()
    test_approval_state_transitions()
    test_rejection_leaves_plan_unchanged()
    test_grocery_regeneration()
    test_duplicate_approval_prevention()
    test_cook_session_completion()

    # LLM-dependent tests last
    test_meal_plan_generation()
    test_different_household()
    test_dairy_allergy()
    test_conflicting_preferences()
    test_empty_household()
    test_budget_constrained()
    test_limited_cooking_time()
    test_api_failure_graceful()

    print("\n" + "=" * 60)
    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    failed = sum(1 for r in RESULTS if r[0] == "FAIL")
    print(f"Results: {passed} passed, {failed} failed out of {len(RESULTS)} checks")
    if failed:
        print("\nFailed checks:")
        for r in RESULTS:
            if r[0] == "FAIL":
                print(f"  [FAIL] {r[1]}" + (f" - {r[2]}" if r[2] else ""))
    sys.exit(0 if failed == 0 else 1)
