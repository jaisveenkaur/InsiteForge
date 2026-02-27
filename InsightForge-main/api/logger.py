"""
Structured logging for the research agent API.
Provides JSON-formatted logs for all API activities and analysis runs.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_event(self, event_type: str, **kwargs):
        """Log a structured event as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))

    def log_api_request(self, client_id: str, endpoint: str, method: str, brief: Dict[str, Any]):
        """Log API request."""
        self.log_event(
            "api_request",
            client_id=client_id,
            endpoint=endpoint,
            method=method,
            mode=brief.get("mode"),
            business_goal=brief.get("business_goal"),
        )

    def log_analysis_start(self, client_id: str, brief: Dict[str, Any]):
        """Log analysis start."""
        self.log_event(
            "analysis_start",
            client_id=client_id,
            mode=brief.get("mode"),
            scope=brief.get("scope", {}).get("value"),
        )

    def log_analysis_complete(self, client_id: str, confidence: int, completeness: str):
        """Log analysis completion."""
        self.log_event(
            "analysis_complete",
            client_id=client_id,
            confidence=confidence,
            completeness=completeness,
        )

    def log_error(self, client_id: str, error: str, context: Optional[Dict] = None):
        """Log error."""
        self.log_event(
            "error",
            client_id=client_id,
            error=error,
            context=context or {},
        )

    def log_security_event(self, event: str, client_id: str, details: Optional[Dict] = None):
        """Log security-related events."""
        self.log_event(
            "security_event",
            event=event,
            client_id=client_id,
            details=details or {},
        )


logger = StructuredLogger("ecommerce_agent")
