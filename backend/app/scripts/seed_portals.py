"""Register a demo complaint portal for every department, plus a default portal.

The portals are the local demo pages served by app/routers/demo_portal.py, so the
browser extension's "fill the complaint portal" path works end to end. Existing portals
are left alone unless --replace is given; an admin can point a department at a real
portal later from the admin console (Complaint portals) or with PUT /portals.

Usage (from backend/):
    uv run python -m app.scripts.seed_portals [--base-url http://localhost:8000] [--replace]
"""

import argparse
import asyncio
import re

from sqlalchemy import select

from app.database import SessionLocal
from app.models import ComplaintPortal, Department
from app.routers.demo_portal import DEMO_FIELD_MAP, DEMO_REFERENCE_SELECTOR


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "general"


async def main(base_url: str, replace: bool) -> None:
    base_url = base_url.rstrip("/")
    async with SessionLocal() as db:
        departments = list(await db.scalars(select(Department).order_by(Department.name)))
        targets: list[tuple[Department | None, str]] = [(d, d.name) for d in departments] + [(None, "General")]
        for department, name in targets:
            clause = (ComplaintPortal.department_id == department.id if department
                      else ComplaintPortal.department_id.is_(None))
            portal = await db.scalar(select(ComplaintPortal).where(clause))
            if portal is not None and not replace:
                print(f"skip (exists): {name} -> {portal.url}")
                continue
            if portal is None:
                portal = ComplaintPortal(department_id=department.id if department else None)
                db.add(portal)
            portal.name = f"{name} complaints (demo)"
            portal.url = f"{base_url}/demo-portal/{slug(name)}"
            portal.field_map = dict(DEMO_FIELD_MAP)
            portal.reference_selector = DEMO_REFERENCE_SELECTOR
            portal.active = True
            print(f"registered: {name} -> {portal.url}")
        await db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--replace", action="store_true", help="overwrite portals that already exist")
    args = parser.parse_args()
    asyncio.run(main(args.base_url, args.replace))
