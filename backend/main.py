import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import engine, get_session, init_db
from models import HouseholdMember, MealPlan, GroceryList, CookSession, ConversationMessage, ApprovalRequest
from tools.grocery import consolidate_grocery_list, simulate_instamart_order

app = FastAPI(title="Anyaa Kitchen OS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Pydantic Request Models ----

class HouseholdMemberCreate(BaseModel):
    name: str
    dietary_restrictions: List[str] = []
    allergies: List[str] = []
    preferences: List[str] = []


class MealPlanCreate(BaseModel):
    week_start: str
    meals: Optional[dict] = None


class CookSessionCreate(BaseModel):
    meal_plan_id: int
    day: str
    meal_name: str


class PlannerChatRequest(BaseModel):
    message: str


class CookChatRequest(BaseModel):
    message: str
    cook_session_id: int


# ---- Startup ----

@app.on_event("startup")
def on_startup():
    init_db()


# ---- Household Routes ----

@app.get("/household")
def get_household(session: Session = Depends(get_session)):
    members = session.exec(select(HouseholdMember)).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "dietary_restrictions": json.loads(m.dietary_restrictions),
            "allergies": json.loads(m.allergies),
            "preferences": json.loads(m.preferences)
        }
        for m in members
    ]


@app.post("/household")
def add_member(member: HouseholdMemberCreate, session: Session = Depends(get_session)):
    new_member = HouseholdMember(
        name=member.name,
        dietary_restrictions=json.dumps(member.dietary_restrictions),
        allergies=json.dumps(member.allergies),
        preferences=json.dumps(member.preferences)
    )
    session.add(new_member)
    session.commit()
    session.refresh(new_member)
    return {"id": new_member.id, "name": new_member.name}


# ---- Meal Plan Routes ----

@app.get("/meal-plans")
def list_meal_plans(session: Session = Depends(get_session)):
    plans = session.exec(select(MealPlan).order_by(MealPlan.id.desc())).all()
    return [
        {"id": p.id, "week_start": p.week_start, "status": p.status}
        for p in plans
    ]


@app.get("/meal-plans/{plan_id}")
def get_meal_plan(plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(MealPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    return {
        "id": plan.id,
        "week_start": plan.week_start,
        "status": plan.status,
        "meals": json.loads(plan.meals)
    }


@app.post("/meal-plans")
def create_meal_plan(data: MealPlanCreate, session: Session = Depends(get_session)):
    from tools.meal_tools import DEMO_MEAL_PLAN
    meals = data.meals or DEMO_MEAL_PLAN
    plan = MealPlan(
        week_start=data.week_start,
        status="planning",
        meals=json.dumps(meals)
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return {"id": plan.id, "week_start": plan.week_start, "status": plan.status}


@app.put("/meal-plans/{plan_id}/approve")
def approve_meal_plan(plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(MealPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    plan.status = "approved"
    session.add(plan)
    session.commit()
    return {"id": plan.id, "status": plan.status, "message": "Meal plan approved!"}


# ---- Grocery List Routes ----

@app.get("/grocery-lists/{meal_plan_id}")
def get_grocery_list(meal_plan_id: int, session: Session = Depends(get_session)):
    grocery = session.exec(
        select(GroceryList).where(GroceryList.meal_plan_id == meal_plan_id)
    ).first()
    if not grocery:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return {
        "id": grocery.id,
        "meal_plan_id": grocery.meal_plan_id,
        "items": json.loads(grocery.items),
        "status": grocery.status
    }


@app.post("/grocery-lists/{meal_plan_id}/generate")
def generate_grocery_list(meal_plan_id: int, session: Session = Depends(get_session)):
    plan = session.get(MealPlan, meal_plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    meals = json.loads(plan.meals)
    items = consolidate_grocery_list(meals)

    # Check if grocery list exists
    existing = session.exec(
        select(GroceryList).where(GroceryList.meal_plan_id == meal_plan_id)
    ).first()

    if existing:
        existing.items = json.dumps(items)
        existing.status = "pending"
        session.add(existing)
        session.commit()
        session.refresh(existing)
        grocery = existing
    else:
        grocery = GroceryList(
            meal_plan_id=meal_plan_id,
            items=json.dumps(items),
            status="pending"
        )
        session.add(grocery)
        session.commit()
        session.refresh(grocery)

    return {
        "id": grocery.id,
        "meal_plan_id": grocery.meal_plan_id,
        "items": items,
        "status": grocery.status
    }


@app.post("/grocery-lists/{meal_plan_id}/order")
def order_groceries(meal_plan_id: int, session: Session = Depends(get_session)):
    grocery = session.exec(
        select(GroceryList).where(GroceryList.meal_plan_id == meal_plan_id)
    ).first()
    if not grocery:
        raise HTTPException(status_code=404, detail="Grocery list not found")

    items = json.loads(grocery.items)
    result = simulate_instamart_order(items)

    grocery.status = "ordered"
    session.add(grocery)
    session.commit()

    return result


# ---- Cook Session Routes ----

@app.get("/cook-sessions")
def list_cook_sessions(session: Session = Depends(get_session)):
    sessions = session.exec(select(CookSession).order_by(CookSession.id.desc())).all()
    return [
        {
            "id": s.id,
            "meal_plan_id": s.meal_plan_id,
            "day": s.day,
            "meal_name": s.meal_name,
            "status": s.status,
            "outcome_meal": s.outcome_meal,
            "outcome_notes": s.outcome_notes,
            "human_interventions": s.human_interventions,
            "completed_at": s.completed_at,
        }
        for s in sessions
    ]


@app.post("/cook-sessions")
def start_cook_session(data: CookSessionCreate, session: Session = Depends(get_session)):
    cook_session = CookSession(
        meal_plan_id=data.meal_plan_id,
        day=data.day,
        meal_name=data.meal_name,
        status="active"
    )
    session.add(cook_session)
    session.commit()
    session.refresh(cook_session)
    return {
        "id": cook_session.id,
        "day": cook_session.day,
        "meal_name": cook_session.meal_name,
        "status": cook_session.status
    }


@app.get("/cook-sessions/{session_id}")
def get_cook_session(session_id: int, session: Session = Depends(get_session)):
    cook_session = session.get(CookSession, session_id)
    if not cook_session:
        raise HTTPException(status_code=404, detail="Cook session not found")
    return {
        "id": cook_session.id,
        "meal_plan_id": cook_session.meal_plan_id,
        "day": cook_session.day,
        "meal_name": cook_session.meal_name,
        "status": cook_session.status,
        "notes": cook_session.notes,
        "substitutions": json.loads(cook_session.substitutions)
    }


# ---- Chat Routes ----

@app.post("/chat/planner")
def chat_planner(request: PlannerChatRequest, session: Session = Depends(get_session)):
    from agents.planner import PlannerAgent
    agent = PlannerAgent(db_session=session)
    response = agent.chat(request.message)
    return {"response": response}


@app.post("/chat/cook")
def chat_cook(request: CookChatRequest, session: Session = Depends(get_session)):
    from agents.cook import CookAgent
    agent = CookAgent(db_session=session)
    response = agent.chat(request.message, request.cook_session_id)
    return {"response": response}


# ---- Conversation History ----

@app.get("/conversations/{session_type}")
def get_conversations(session_type: str, session: Session = Depends(get_session)):
    messages = session.exec(
        select(ConversationMessage)
        .where(ConversationMessage.session_type == session_type)
        .order_by(ConversationMessage.timestamp)
    ).all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp
        }
        for m in messages
    ]


# ---- Cook Session Completion ----

class SessionOutcome(BaseModel):
    outcome_meal: str
    outcome_notes: str
    followed_plan: bool = True


@app.post("/cook-sessions/{session_id}/complete")
def complete_cook_session(session_id: int, body: SessionOutcome, session: Session = Depends(get_session)):
    """Household or cook marks a session done and records what actually happened."""
    cook_session = session.get(CookSession, session_id)
    if not cook_session:
        raise HTTPException(status_code=404, detail="Cook session not found")
    notes = cook_session.notes or ""
    notes_count = notes.count("[APPROVAL NEEDED]") + notes.count("[APPROVED]") + notes.count("[REJECTED]")
    db_count = len(session.exec(
        select(ApprovalRequest).where(ApprovalRequest.cook_session_id == session_id)
    ).all())
    interventions = max(notes_count, db_count)
    cook_session.status = "completed"
    cook_session.outcome_meal = body.outcome_meal
    cook_session.outcome_notes = body.outcome_notes
    cook_session.human_interventions = interventions
    cook_session.completed_at = datetime.utcnow().isoformat()
    session.add(cook_session)
    session.commit()
    return {
        "id": cook_session.id,
        "status": "completed",
        "outcome_meal": cook_session.outcome_meal,
        "followed_plan": body.followed_plan,
        "human_interventions": interventions,
        "message": "Session outcome recorded."
    }


# ---- Operational Analytics ----

@app.get("/analytics")
def get_analytics(session: Session = Depends(get_session)):
    """Operational metrics: automation rate, common exceptions, intervention frequency."""
    all_sessions = session.exec(select(CookSession)).all()
    completed = [s for s in all_sessions if s.status == "completed"]

    total = len(completed)
    if total == 0:
        return {
            "completed_sessions": 0,
            "automation_rate_pct": None,
            "avg_human_interventions": None,
            "sessions_with_substitutions": 0,
            "sessions_deviated_from_plan": 0,
            "message": "No completed sessions yet. Cook and complete a session to see metrics."
        }

    total_interventions = sum(s.human_interventions for s in completed)
    zero_intervention = sum(1 for s in completed if s.human_interventions == 0)
    automation_rate = round(zero_intervention / total * 100, 1)

    sessions_with_subs = sum(1 for s in completed if json.loads(s.substitutions))
    deviated = sum(1 for s in completed if s.outcome_meal and s.outcome_meal != s.meal_name)

    # Collect all substitutions made
    all_subs = []
    for s in completed:
        subs = json.loads(s.substitutions)
        all_subs.extend(subs)

    missing_ingredients = [sub.get("missing") for sub in all_subs if sub.get("missing")]
    common_missing = Counter(missing_ingredients).most_common(5)

    return {
        "completed_sessions": total,
        "automation_rate_pct": automation_rate,
        "avg_human_interventions": round(total_interventions / total, 2),
        "sessions_with_substitutions": sessions_with_subs,
        "sessions_deviated_from_plan": deviated,
        "common_missing_ingredients": [{"ingredient": k, "count": v} for k, v in common_missing],
        "insight": (
            f"{automation_rate}% of cook sessions completed without any human approval needed. "
            f"Most common friction: {common_missing[0][0] if common_missing else 'none recorded'}."
        )
    }


# ---- Cook Approval Workflow (legacy, text-parsing based) ----

class ApprovalDecision(BaseModel):
    decision: str  # "approve" or "reject"
    reason: Optional[str] = None


@app.get("/cook-sessions/{session_id}/approvals")
def get_pending_approvals(session_id: int, session: Session = Depends(get_session)):
    """List all approval requests for this session (structured + legacy notes)."""
    cook_session = session.get(CookSession, session_id)
    if not cook_session:
        raise HTTPException(status_code=404, detail="Cook session not found")

    # Return structured ApprovalRequest records if available
    structured = session.exec(
        select(ApprovalRequest).where(ApprovalRequest.cook_session_id == session_id)
    ).all()

    if structured:
        return {
            "cook_session_id": session_id,
            "approvals": [
                {
                    "id": a.id,
                    "issue": a.issue,
                    "proposed_change": a.proposed_change,
                    "status": a.status,
                    "requested_at": a.requested_at,
                    "decided_at": a.decided_at,
                    "decision_reason": a.decision_reason,
                }
                for a in structured
            ]
        }

    # Fallback: legacy text parsing
    notes = cook_session.notes or ""
    approvals = []
    for i, line in enumerate(notes.splitlines()):
        if "[APPROVAL NEEDED]" in line:
            approvals.append({"index": i, "request": line.replace("[APPROVAL NEEDED]", "").strip(), "status": "pending"})
        elif "[APPROVED]" in line or "[REJECTED]" in line:
            tag = "[APPROVED]" if "[APPROVED]" in line else "[REJECTED]"
            approvals.append({"index": i, "request": line.replace(tag, "").strip(), "status": tag[1:-1].lower()})
    return {"cook_session_id": session_id, "approvals": approvals}


@app.post("/cook-sessions/{session_id}/approvals/{approval_index}")
def decide_approval_legacy(
    session_id: int,
    approval_index: int,
    body: ApprovalDecision,
    session: Session = Depends(get_session)
):
    """Legacy: approve/reject by line index in session notes."""
    cook_session = session.get(CookSession, session_id)
    if not cook_session:
        raise HTTPException(status_code=404, detail="Cook session not found")
    if body.decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")

    lines = (cook_session.notes or "").splitlines()
    if approval_index >= len(lines) or "[APPROVAL NEEDED]" not in lines[approval_index]:
        raise HTTPException(status_code=404, detail="Pending approval not found at that index")

    tag = "[APPROVED]" if body.decision == "approve" else "[REJECTED]"
    reason_suffix = f" (Reason: {body.reason})" if body.reason else ""
    lines[approval_index] = lines[approval_index].replace("[APPROVAL NEEDED]", tag) + reason_suffix
    cook_session.notes = "\n".join(lines)
    session.add(cook_session)
    session.commit()

    return {
        "cook_session_id": session_id,
        "decision": body.decision,
        "message": f"Change {'approved' if body.decision == 'approve' else 'rejected'} by household.",
        "note": lines[approval_index]
    }


# ---- Structured Approval Endpoints ----

@app.get("/approvals")
def list_approvals(status: Optional[str] = None, session: Session = Depends(get_session)):
    """List all approval requests, optionally filtered by status."""
    query = select(ApprovalRequest)
    if status:
        query = query.where(ApprovalRequest.status == status)
    approvals = session.exec(query.order_by(ApprovalRequest.id.desc())).all()
    return [
        {
            "id": a.id,
            "cook_session_id": a.cook_session_id,
            "meal_plan_id": a.meal_plan_id,
            "day": a.day,
            "meal_type": a.meal_type,
            "issue": a.issue,
            "original_ingredient": a.original_ingredient,
            "proposed_change": a.proposed_change,
            "reason": a.reason,
            "requested_by": a.requested_by,
            "requested_at": a.requested_at,
            "status": a.status,
            "decided_by": a.decided_by,
            "decided_at": a.decided_at,
            "decision_reason": a.decision_reason,
        }
        for a in approvals
    ]


@app.get("/approvals/{approval_id}")
def get_approval(approval_id: int, session: Session = Depends(get_session)):
    """Get a single approval request."""
    approval = session.get(ApprovalRequest, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return {
        "id": approval.id,
        "cook_session_id": approval.cook_session_id,
        "meal_plan_id": approval.meal_plan_id,
        "day": approval.day,
        "meal_type": approval.meal_type,
        "issue": approval.issue,
        "original_ingredient": approval.original_ingredient,
        "proposed_change": approval.proposed_change,
        "reason": approval.reason,
        "requested_by": approval.requested_by,
        "requested_at": approval.requested_at,
        "status": approval.status,
        "decided_by": approval.decided_by,
        "decided_at": approval.decided_at,
        "decision_reason": approval.decision_reason,
    }


class ApprovalDecideBody(BaseModel):
    decision: str  # "approve" or "reject"
    reason: Optional[str] = ""
    decided_by: Optional[str] = "household"


@app.post("/approvals/{approval_id}/decide")
def decide_approval(approval_id: int, body: ApprovalDecideBody, session: Session = Depends(get_session)):
    """Household approves or rejects a structured approval request."""
    approval = session.get(ApprovalRequest, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")

    if approval.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Approval already decided: status is '{approval.status}'. Cannot decide again."
        )

    if body.decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision must be 'approve' or 'reject'")

    grocery_regenerated = False

    if body.decision == "approve" and approval.day and approval.meal_type and approval.proposed_change:
        # Safety validation before applying any meal substitution
        if not approval.meal_plan_id:
            raise HTTPException(status_code=400, detail="Cannot apply change: meal_plan_id not set on this approval")

        members_raw = session.exec(select(HouseholdMember)).all()
        member_data = [
            {
                "name": m.name,
                "dietary_restrictions": json.loads(m.dietary_restrictions),
                "allergies": json.loads(m.allergies),
                "preferences": json.loads(m.preferences),
            }
            for m in members_raw
        ]

        from tools.meal_tools import validate_meal_against_household
        safety = validate_meal_against_household(approval.proposed_change, member_data)
        if not safety["safe"]:
            violation_summary = "; ".join(
                f"{v['member']} - {v.get('allergen', v.get('restriction', 'unknown'))} ({v['severity']})"
                for v in safety["violations"]
            )
            approval.status = "rejected"
            approval.decided_by = body.decided_by or "household"
            approval.decided_at = datetime.utcnow().isoformat()
            approval.decision_reason = f"Safety validation failed: {violation_summary}"
            session.add(approval)
            session.commit()
            session.refresh(approval)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Proposed change failed safety validation and was auto-rejected",
                    "violations": safety["violations"],
                    "decision_reason": approval.decision_reason,
                    "approval_id": approval.id,
                    "status": "rejected"
                }
            )

    approved_as = "approved" if body.decision == "approve" else "rejected"
    try:
        approval.status = approved_as
        approval.decided_by = body.decided_by or "household"
        approval.decided_at = datetime.utcnow().isoformat()
        approval.decision_reason = body.reason or ""
        session.add(approval)

        # If approved and proposed_change looks like a meal swap, update the plan
        if approved_as == "approved" and approval.day and approval.meal_type and approval.proposed_change:
            if not approval.meal_plan_id:
                raise HTTPException(status_code=400, detail="Cannot apply change: meal_plan_id not set")
            plan = session.get(MealPlan, approval.meal_plan_id)
            if plan:
                meals = json.loads(plan.meals)
                day = approval.day
                meal_type = approval.meal_type
                if day in meals and meal_type in meals[day]:
                    meals[day][meal_type] = approval.proposed_change
                    plan.meals = json.dumps(meals)
                    session.add(plan)

                    # Regenerate grocery list
                    existing_grocery = session.exec(
                        select(GroceryList).where(GroceryList.meal_plan_id == approval.meal_plan_id)
                    ).first()
                    if existing_grocery:
                        items = consolidate_grocery_list(meals)
                        existing_grocery.items = json.dumps(items)
                        existing_grocery.status = "pending"
                        session.add(existing_grocery)
                        grocery_regenerated = True

        session.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply approval decision: {str(e)}")

    session.refresh(approval)
    return {
        "id": approval.id,
        "status": approval.status,
        "decided_by": approval.decided_by,
        "decided_at": approval.decided_at,
        "decision_reason": approval.decision_reason,
        "grocery_regenerated": grocery_regenerated,
        "message": f"Request {'approved' if approval.status == 'approved' else 'rejected'} by {approval.decided_by}."
    }


# ---- Static Files ----

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
