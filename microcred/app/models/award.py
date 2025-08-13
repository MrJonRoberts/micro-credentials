from ..extensions import db
from ..routes.main import index


class Award(db.Model):
    __tablename__ = "awards"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)  # stable id for URLs/API
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    points = db.Column(db.Integer, nullable=False, default=0)
    criteria = db.Column(db.Text, nullable=True)

    # achievements: one-to-many via Achievement.award relationship
    achievements = db.relationship("Achievement", back_populates="award", lazy="dynamic")

    def image_url(self, base: str | None) -> str | None:
        if not self.image_filename:
            return None
        return f"{base.rstrip('/')}/{self.image_filename}" if base else self.image_filename

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Award {self.slug}:{self.name} ({self.points} pts)>"
