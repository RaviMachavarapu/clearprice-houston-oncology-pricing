from __future__ import annotations

from fastapi import APIRouter

from src.reference_data.drugs import load_drugs

router = APIRouter()


@router.get("/api/drugs")
def get_drugs() -> dict:
    """Return the 33 reference Drug records (code, name, category) per FR-001."""
    drugs = load_drugs()
    return {
        "drugs": [
            {"code": d.code, "name": d.name, "category": d.category}
            for d in drugs
        ]
    }
