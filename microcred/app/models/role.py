from ..extensions import db

class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)  # "participant" | "issuer" | "admin"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role {self.name}>"
