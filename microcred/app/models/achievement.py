from datetime import datetime
from ..extensions import db

class Achievement(db.Model):
    __tablename__ = "achievements"
    __table_args__ = (
        db.UniqueConstraint("participant_id", "award_id", name="uq_participant_award_once"),
    )

    id = db.Column(db.Integer, primary_key=True)

    participant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    award_id = db.Column(db.Integer, db.ForeignKey("awards.id"), nullable=False, index=True)
    issued_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    issued_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    note = db.Column(db.String(255), nullable=True)

    # Relationships
    participant = db.relationship("User", foreign_keys=[participant_id], back_populates="achievements")
    award = db.relationship("Award", back_populates="achievements")
    issued_by = db.relationship("User", foreign_keys=[issued_by_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Achievement user={self.participant_id} award={self.award_id} at={self.issued_at:%Y-%m-%d}>"
