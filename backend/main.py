import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db import Base, engine, get_db
from models import User
from models_opt import OptimizationRun, HourlyFlow
from schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    OptimizeRequest,
    OptimizeResponse,
)
from security import hash_password, verify_password
from jwt_utils import create_access_token
from auth_dep import get_current_user
from optimizer import schedule_water_flow

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stay Hydrated Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for student project/demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Stay Hydrated backend is running"}


# ---------------- AUTH ----------------

@app.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})
    return TokenResponse(access_token=token)


@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }


# ---------------- OPTIMIZATION ----------------

@app.post("/optimize", response_model=OptimizeResponse)
def optimize(
    payload: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    node_set = set(payload.nodes)
    if payload.source not in node_set:
        raise HTTPException(status_code=400, detail="Source node not found in nodes list")
    if payload.sink not in node_set:
        raise HTTPException(status_code=400, detail="Sink node not found in nodes list")
    if payload.source == payload.sink:
        raise HTTPException(status_code=400, detail="Source and sink must be different")

    for e in payload.edges:
        if e.from_node not in node_set or e.to_node not in node_set:
            raise HTTPException(
                status_code=400,
                detail=f"Edge contains invalid node: {e.from_node} -> {e.to_node}",
            )

    result = schedule_water_flow(payload.model_dump())

    run = OptimizationRun(
        user_id=current_user.id,
        source_node=payload.source,
        sink_node=payload.sink,
        total_demand=payload.total_demand,
        delivered_volume=result["delivered_volume"],
        hours=payload.hours,
        total_cost=result["total_cost"],
        status=result["status"],
        nodes_json=json.dumps(payload.nodes),
        edges_json=json.dumps([e.model_dump() for e in payload.edges]),
        result_json=json.dumps(result),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    for hour_block in result["schedule"]:
        for flow_item in hour_block["flows"]:
            row = HourlyFlow(
                run_id=run.id,
                hour=hour_block["hour"],
                edge_key=f'{flow_item["from_node"]}->{flow_item["to_node"]}',
                from_node=flow_item["from_node"],
                to_node=flow_item["to_node"],
                flow=flow_item["flow"],
                effective_cost=flow_item["effective_cost"],
                edge_cost_total=flow_item["edge_cost_total"],
            )
            db.add(row)

    db.commit()

    result["run_id"] = run.id
    return result


@app.get("/optimizations")
def list_optimizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    runs = (
        db.query(OptimizationRun)
        .filter(OptimizationRun.user_id == current_user.id)
        .order_by(OptimizationRun.id.desc())
        .all()
    )

    output = []
    for r in runs:
        output.append(
            {
                "run_id": r.id,
                "source": r.source_node,
                "sink": r.sink_node,
                "total_demand": r.total_demand,
                "delivered_volume": r.delivered_volume,
                "hours": r.hours,
                "total_cost": r.total_cost,
                "status": r.status,
                "created_at": r.created_at,
            }
        )
    return output


@app.get("/optimizations/{run_id}")
def get_optimization(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = (
        db.query(OptimizationRun)
        .filter(
            OptimizationRun.id == run_id,
            OptimizationRun.user_id == current_user.id,
        )
        .first()
    )

    if not run:
        raise HTTPException(status_code=404, detail="Optimization run not found")

    return json.loads(run.result_json)