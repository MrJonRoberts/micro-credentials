from typing import Tuple, Optional
from ..extensions import db
from ..models import Achievement, Award, User
from .criteria_service import CriteriaService
from .audit_service import AuditService

class AwardService:
    def __init__(self, criteria: Optional[CriteriaService] = None, audit: Optional[AuditService] = None):
        self.criteria = criteria or CriteriaService()
        self.audit = audit or AuditService()

    def grant_award(self, participant_id: int, award_id: int, *, issued_by_id: int, note: str = "") -> Tuple[bool, str]:
        # Existence checks
        participant = User.query.get(participant_id)
        award = Award.query.get(award_id)
        issuer = User.query.get(issued_by_id)
        if not all([participant, award, issuer]):
            return False, "Invalid participant, award, or issuer."

        # Duplicate check
        exists = Achievement.query.filter_by(participant_id=participant_id, award_id=award_id).first()
        if exists:
            return False, "Participant already has this award."

        # Eligibility check (optional rule engine)
        ok, reason = self.criteria.is_eligible(participant, award)
        if not ok:
            return False, f"Not eligible: {reason}"

        # Persist
        ach = Achievement(participant_id=participant_id, award_id=award_id, issued_by_id=issued_by_id, note=note)
        db.session.add(ach)
        db.session.commit()

        # Audit/notify (best‑effort; avoid breaking the transaction)
        self.audit.record("award.granted", {
            "participant_id": participant_id, "award_id": award_id,
            "issued_by_id": issued_by_id, "note": note
        })

        return True, "Award granted."
