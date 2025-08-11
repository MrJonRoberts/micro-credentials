from flask_login import UserMixin
from ..extensions import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from .associations import user_roles

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))

    roles = db.relationship("Role", secondary=user_roles, backref="users", lazy="joined")
    # Fix: Specify foreign_keys to resolve ambiguity
    achievements = db.relationship("Achievement",
                                 foreign_keys="Achievement.participant_id",
                                 back_populates="participant",
                                 lazy="dynamic")

    # --- Password helpers ---
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self) -> str:
        first = (self.first_name or "").strip()
        last = (self.last_name or "").strip()
        return " ".join(p for p in (first, last) if p)

    def has_role(self, *role_names: str) -> bool:
        names = {r.name for r in self.roles}
        return any(rn in names for rn in role_names)



    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"

@login_manager.user_loader
def load_user(user_id: str):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None