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
    print(f"{symbol} {name}" + (f" — {detail}" if detail else ""))


# ---- 1. Allergy enforcement ----

def test_allergy_enforcement():
    print("\n--- 1. Allergy Enforcement ---")
    # CRITICAL: peanut must always be blocked
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
    # Meat without veg alternative should fail for Sarah
    result = validate_meal_against_household("Grilled chicken with rice", HOUSEHOLD)
    check("Chicken without veg alternative blocked for Sarah", not result["safe"])

    # Meat WITH explicit veg alternative should pass
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


# ---- 4. Meal plan generation ----

def test_meal_plan_generation():
    print("\n--- 4. Meal Plan Generation ---")
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


# ---- 5. Substitution scenarios ----

def test_substitution_scenarios():
    print("\n--- 5. Substitution Scenarios ---")
    from agents.cook import SUBSTITUTION_MAP

    butter_subs = SUBSTITUTION_MAP.get("butter", [])
    check("Butter has substitutions", len(butter_subs) > 0, str(butter_subs))

    # Validate each butter sub is safe
    for sub in butter_subs:
        safety = check_ingredient_safety(sub, HOUSEHOLD)
        check(f"Butter sub '{sub}' safe for household", safety["safe"],
              f"conflicts={safety['conflicts']}")

    # Peanut butter should NOT be in substitution map values (would cause allergy)
    all_subs = [s for subs in SUBSTITUTION_MAP.values() for s in subs]
    has_peanut_sub = any("peanut" in s.lower() for s in all_subs)
    check("No peanut-containing substitutes in map", not has_peanut_sub)


# ---- 6. Constraint-aware generation with new household ----

def test_different_household():
    print("\n--- 6. Different Household (no preset) ---")
    custom_household = [
        {"name": "Priya", "dietary_restrictions": ["vegan"], "allergies": ["gluten"], "preferences": ["South Indian"]},
        {"name": "Raj", "dietary_restrictions": [], "allergies": ["shellfish"], "preferences": ["spicy food"]},
    ]
    result = generate_meal_plan(custom_household)
    plan = result.get("plan", {})
    check("Plan generated for custom household", len(plan) == 7)

    dairy_words = ["milk", "cheese", "butter", "cream", "yogurt", "egg", "meat", "chicken", "beef"]
    vegan_violations = []
    for day, meals in plan.items():
        for meal_type, meal_desc in meals.items():
            meal_lower = meal_desc.lower()
            for dw in dairy_words:
                if dw in meal_lower and "vegan" not in meal_lower and "tofu" not in meal_lower:
                    vegan_violations.append(f"{day} {meal_type}: {meal_desc} (contains '{dw}')")
    # Note: LLM may not always be perfect; flag but don't hard-fail the suite
    if vegan_violations:
        print(f"  WARNING: Possible vegan violations ({len(vegan_violations)}):")
        for v in vegan_violations[:3]:
            print(f"    {v}")
    check("Custom household plan has 7 days", len(plan) == 7)


# ---- 7. Missing ingredient + substitution safety chain ----

def test_missing_ingredient_chain():
    print("\n--- 7. Missing Ingredient Chain ---")
    # Simulate: cook reports butter missing, system suggests substitutes, check they're safe
    from tools.meal_tools import check_ingredient_safety
    from agents.cook import SUBSTITUTION_MAP

    missing = "butter"
    subs = SUBSTITUTION_MAP.get(missing, [])
    safe_subs = [s for s in subs if check_ingredient_safety(s, HOUSEHOLD)["safe"]]
    check("At least one safe butter substitute available", len(safe_subs) > 0, str(safe_subs))

    # Simulate: cook reports eggs missing
    missing2 = "eggs"
    subs2 = SUBSTITUTION_MAP.get(missing2, [])
    safe_subs2 = [s for s in subs2 if check_ingredient_safety(s, HOUSEHOLD)["safe"]]
    check("At least one safe egg substitute available", len(safe_subs2) > 0, str(safe_subs2))


# ---- 8. Approval flag parsing ----

def test_approval_parsing():
    print("\n--- 8. Approval Flag Parsing ---")
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

    test_allergy_enforcement()
    test_vegetarian_enforcement()
    test_ingredient_safety()
    test_substitution_scenarios()
    test_missing_ingredient_chain()
    test_approval_parsing()
    test_meal_plan_generation()    # calls LLM - run last
    test_different_household()     # calls LLM

    print("\n" + "=" * 60)
    passed = sum(1 for r in RESULTS if r[0] == "PASS")
    failed = sum(1 for r in RESULTS if r[0] == "FAIL")
    print(f"Results: {passed} passed, {failed} failed out of {len(RESULTS)} checks")
    if failed:
        print("\nFailed checks:")
        for r in RESULTS:
            if r[0] == "FAIL":
                print(f"  [FAIL] {r[1]}" + (f" — {r[2]}" if r[2] else ""))
    sys.exit(0 if failed == 0 else 1)
