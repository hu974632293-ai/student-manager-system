from sqlalchemy.orm import Session

from app.models.refresh_token import UserRefreshToken


class RefreshTokenDAO:
    def create(self, db: Session, data: dict):
        token = UserRefreshToken(**data)
        db.add(token)
        return token

    def get_by_hash(self, db: Session, token_hash: str):
        return db.query(UserRefreshToken).filter(UserRefreshToken.token_hash == token_hash).first()

    def revoke(self, db: Session, token: UserRefreshToken, revoked_at, replaced_by_jti=None):
        token.revoked_at = revoked_at
        token.replaced_by_jti = replaced_by_jti
        return token

    def revoke_all_for_user(self, db: Session, user_id: int, revoked_at):
        count = (
            db.query(UserRefreshToken)
            .filter(UserRefreshToken.user_id == user_id, UserRefreshToken.revoked_at.is_(None))
            .update({"revoked_at": revoked_at}, synchronize_session=False)
        )
        return count


refresh_token_dao = RefreshTokenDAO()
