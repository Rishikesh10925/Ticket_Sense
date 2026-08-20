"""Create one demo account per role, for local dev and the Week 3 mentor demo.

Engineer/Admin accounts can't be created via POST /auth/register (End User only,
see app/routers/auth.py), so this script is the only way to get a login for all
three roles locally. Also seeds the five target departments if they don't exist,
since users.department_id needs a real row to point at.

Usage (from backend/):
    uv run python -m app.scripts.seed_demo_users
"""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import Department, User

DEMO_PASSWORD = "Demo@123"
DEPARTMENTS = ["SAP", "Networking", "Cloud", "Database", "HR"]
DEMO_USERS = [
    {"email": "customer@demo.local", "full_name": "Demo Customer", "role": "end_user", "department": None},
    {
        "email": "engineer@demo.local",
        "full_name": "Demo Engineer",
        "role": "department_engineer",
        "department": "Networking",
    },
    {"email": "admin@demo.local", "full_name": "Demo Admin", "role": "admin", "department": None},
]


async def main() -> None:
    async with SessionLocal() as db:
        departments: dict[str, Department] = {}
        for name in DEPARTMENTS:
            existing = await db.scalar(select(Department).where(Department.name == name))
            if existing is None:
                existing = Department(name=name)
                db.add(existing)
                await db.flush()
            departments[name] = existing

        for spec in DEMO_USERS:
            existing_user = await db.scalar(select(User).where(User.email == spec["email"]))
            if existing_user is not None:
                print(f"skip (exists): {spec['email']}")
                continue

            department = departments[spec["department"]] if spec["department"] else None
            user = User(
                email=spec["email"],
                full_name=spec["full_name"],
                role=spec["role"],
                department_id=department.id if department else None,
                hashed_password=hash_password(DEMO_PASSWORD),
            )
            db.add(user)
            print(f"created: {spec['email']} ({spec['role']})")

        await db.commit()

    print(f"\nAll demo accounts use password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
