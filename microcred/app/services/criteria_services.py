from typing import Tuple
from ..models import User, Award

class CriteriaService:
    def is_eligible(self, user: User, award: Award) -> Tuple[bool, str]:
        # Simple default: everything is achievable unless award.criteria encodes rules
        # You can parse a criteria DSL, check points, prior awards, enrolment, etc.
        # Example rule: disallow if award.points > 100 for non‑admin issuers (placeholder)
        return True, "OK"
