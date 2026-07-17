"""Seed default admin and student accounts."""

import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import User, UserRole
from app.security.auth import hash_password

logger = logging.getLogger(__name__)
settings = get_settings()


async def seed_users() -> None:
    async with AsyncSessionLocal() as db:
        for email, password, role in [
            (settings.admin_email.lower(), settings.admin_password, UserRole.ADMIN.value),
            (settings.student_email.lower(), settings.student_password, UserRole.STUDENT.value),
        ]:
            result = await db.execute(select(User).where(User.email == email))
            existing = result.scalar_one_or_none()
            if existing:
                continue
            db.add(
                User(
                    email=email,
                    password_hash=hash_password(password),
                    role=role,
                )
            )
            logger.info("Created %s user: %s", role, email)
        await db.commit()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_users())


if __name__ == "__main__":
    main()
