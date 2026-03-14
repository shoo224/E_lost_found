# matching_job.py - Hourly background matching job (APScheduler)
# Run matching for all open lost and found items

import logging
from app.services.matcher import run_hourly_matching

logger = logging.getLogger(__name__)


def hourly_matching_job():
    """Called every hour by APScheduler."""
    try:
        run_hourly_matching()
        logger.info("Hourly matching job completed")
    except Exception as e:
        logger.exception("Hourly matching job failed: %s", e)
