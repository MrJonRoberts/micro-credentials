# app/models/icon.py
from microcred.app.extensions import db
from sqlalchemy import func, UniqueConstraint, Index

class Icon(db.Model):
    __tablename__ = 'icons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)  # human-friendly key
    category = db.Column(db.String(120), nullable=False)           # becomes directory under /static/Icons
    filename = db.Column(db.String(255), nullable=False)           # stored file name only (not path)

    # Optional: keep a cached url if you prefer. Otherwise compute it.
    # url = db.Column(db.String(512), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('category', 'filename', name='uq_icon_category_filename'),
        Index('ix_icon_category_name', 'category', 'name'),
        Index('ix_icon_name_ilike', 'name'),  # helps LIKE/ILIKE
    )

    # def compute_url(self) -> str:
    #     return f"/static/Icons/{self.category}/{self.filename}"

    def __repr__(self):
        return f"<Icon {self.id} {self.name} -> {self.compute_url()}>"
