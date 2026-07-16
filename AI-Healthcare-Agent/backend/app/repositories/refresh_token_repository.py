import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: Session):
        super().__init__(db, RefreshToken)

    def get_by_jti(self, jti: str) -> RefreshToken | None:
        query = select(RefreshToken).where(RefreshToken.jti == jti)
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_valid_by_user_id(self, user_id: str | uuid.UUID) -> list[RefreshToken]:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        query = (
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .order_by(RefreshToken.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())

    def revoke_token(self, jti: str) -> bool:
        query = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(
                is_revoked=True,
                revoked_at=datetime.now(timezone.utc),
            )
        )
        result = self.db.execute(query)
        self.db.commit()
        return result.rowcount > 0

    def revoke_all_user_tokens(self, user_id: str | uuid.UUID) -> int:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        query = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False,
            )
            .values(
                is_revoked=True,
                revoked_at=datetime.now(timezone.utc),
            )
        )
        result = self.db.execute(query)
        self.db.commit()
        return result.rowcount

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        query = select(RefreshToken).where(
            RefreshToken.expires_at <= now
        )
        result = self.db.execute(query)
        tokens = result.scalars().all()
        count = 0
        for token in tokens:
            self.db.delete(token)
            count += 1
        self.db.commit()
        return count
