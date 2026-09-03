import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import Department, User
from app.schemas.departments import DepartmentOut, DepartmentThresholdUpdate

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
async def list_departments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Department]:
    result = await db.scalars(select(Department).order_by(Department.name))
    return list(result)


@router.patch("/{department_id}/threshold", response_model=DepartmentOut)
async def update_department_threshold(
    department_id: uuid.UUID,
    body: DepartmentThresholdUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> Department:
    """Sets the confidence score below which the Week 9 gate escalates a ticket for
    this department instead of showing its draft to a reviewer. Existing tickets keep
    whatever threshold was snapshotted onto them at scoring time (Ticket.
    confidence_threshold) — this only changes what new tickets get."""
    department = await db.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Department not found")

    department.confidence_threshold = body.confidence_threshold
    await db.commit()
    await db.refresh(department)
    return department
