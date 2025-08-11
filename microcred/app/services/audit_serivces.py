import logging
logger = logging.getLogger("microcred.audit")

class AuditService:
    def record(self, event: str, payload: dict):
        logger.info("%s %s", event, payload)
