# microcred/app/routes/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from flask_wtf.file import FileField, FileAllowed
import re
from ..models import Award


def slugify(value: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip()).strip("-").lower()
    return s or "award"

class AwardForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    slug = StringField("Slug", validators=[Optional(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=255)])
    points = IntegerField("Points", validators=[NumberRange(min=0)], default=0)
    icon = FileField(
        "Icon (PNG/JPG/WEBP)",
        validators=[FileAllowed(["png", "jpg", "jpeg", "webp"], "Images only")]
    )

class AwardEditForm(AwardForm):
    remove_icon = BooleanField("Remove current icon")

    def validate_slug(self, field):
        # uniqueness check excluding the award being edited
        from flask import request
        award_id = request.view_args.get("award_id")
        if not field.data:
            return
        exists = Award.query.filter(
            Award.slug == field.data,
            Award.id != award_id
        ).first()
        if exists:
            raise ValidationError("That slug is already in use.")