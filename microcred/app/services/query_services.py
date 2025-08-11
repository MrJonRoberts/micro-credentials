from sqlalchemy import func
from ..models import Achievement, Award, User

class QueryService:
    def participant_awards(self, participant_id: int):
        rows = (Achievement.query
                .filter(Achievement.participant_id == participant_id)
                .join(Award)
                .order_by(Achievement.issued_at.desc())
                .all())
        total_points = sum(r.award.points for r in rows)
        return rows, total_points

    def award_holders(self, award_slug: str):
        return (Achievement.query
                .join(Award, Achievement.award_id == Award.id)
                .join(User, Achievement.participant_id == User.id)
                .filter(Award.slug == award_slug)
                .order_by(User.last_name.asc(), User.first_name.asc())
                .all())
