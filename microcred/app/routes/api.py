from flask import Blueprint, jsonify, current_app, url_for
from ..models import User, Award, Achievement

bp = Blueprint("api", __name__, url_prefix="/api")

def award_to_dict(a: Award):
    return {
        "id": a.id,
        "slug": a.slug,
        "name": a.name,
        "description": a.description,
        "image": a.image_url(current_app.config.get("AWARD_IMAGE_BASE", "/static/awards")),  # type: ignore[attr-defined]
        "points": a.points,
        "criteria": a.criteria,
    }

@bp.get("/participants/<int:participant_id>/awards")
def api_participant_awards(participant_id: int):
    user = User.query.get_or_404(participant_id)
    achs = (Achievement.query
            .filter_by(participant_id=user.id)
            .join(Award)
            .order_by(Achievement.issued_at.desc())
            .all())
    return jsonify({
        "participant": {
            "id": user.id,
            "name": user.full_name() if hasattr(user, "full_name") else f"{user.first_name or ''} {user.last_name or ''}".strip(),
            "email": user.email,
        },
        "awards": [{
            "award": award_to_dict(ach.award),
            "issued_at": ach.issued_at.isoformat(),
            "issued_by": {
                "id": ach.issued_by.id if ach.issued_by else None,
                "name": ach.issued_by.full_name() if getattr(ach, "issued_by", None) and hasattr(ach.issued_by, "full_name") else (
                    f"{getattr(ach.issued_by, 'first_name', '')} {getattr(ach.issued_by, 'last_name', '')}".strip() if ach.issued_by else None
                ),
            },
            "detail_url": url_for("api.api_award_for_participant",
                                  participant_id=user.id, award_slug=ach.award.slug, _external=True)
        } for ach in achs]
    })

@bp.get("/participants/<int:participant_id>/awards/<award_slug>")
def api_award_for_participant(participant_id: int, award_slug: str):
    ach = (Achievement.query
           .join(Award)
           .filter(Achievement.participant_id == participant_id, Award.slug == award_slug)
           .first_or_404())
    return jsonify({
        "participant_id": participant_id,
        "award": award_to_dict(ach.award),
        "issued_at": ach.issued_at.isoformat(),
        "issued_by": {
            "id": ach.issued_by.id if ach.issued_by else None,
            "name": ach.issued_by.full_name() if getattr(ach, "issued_by", None) and hasattr(ach.issued_by, "full_name") else (
                f"{getattr(ach.issued_by, 'first_name', '')} {getattr(ach.issued_by, 'last_name', '')}".strip() if ach.issued_by else None
            ),
        },
        "note": ach.note,
    })

@bp.get("/awards")
def api_awards():
    awards = Award.query.order_by(Award.points.desc(), Award.name.asc()).all()
    return jsonify({
        "awards": [{
            **award_to_dict(a),
            "participants_url": url_for("api.api_award_participants", award_slug=a.slug, _external=True)
        } for a in awards]
    })

@bp.get("/awards/<award_slug>/participants")
def api_award_participants(award_slug: str):
    award = Award.query.filter_by(slug=award_slug).first_or_404()
    rows = (Achievement.query
            .filter_by(award_id=award.id)
            .join(User, Achievement.participant_id == User.id)
            .order_by(User.last_name.asc(), User.first_name.asc())
            .all())
    return jsonify({
        "award": award_to_dict(award),
        "participants": [{
            "id": r.participant.id,
            "name": r.participant.full_name() if hasattr(r.participant, "full_name") else f"{r.participant.first_name or ''} {r.participant.last_name or ''}".strip(),
            "email": r.participant.email,
            "issued_at": r.issued_at.isoformat(),
            "issued_by": {
                "id": r.issued_by.id if r.issued_by else None,
                "name": r.issued_by.full_name() if getattr(r, "issued_by", None) and hasattr(r.issued_by, "full_name") else (
                    f"{getattr(r.issued_by, 'first_name', '')} {getattr(r.issued_by, 'last_name', '')}".strip() if r.issued_by else None
                ),
            }
        } for r in rows]
    })
