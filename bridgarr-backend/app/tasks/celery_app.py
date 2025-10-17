"""
Celery Application Configuration
Distributed task queue for background processing
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery app
celery_app = Celery(
    "bridgarr",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.link_refresh",
        "app.tasks.torrent_check"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks to prevent memory leaks
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    # Refresh expiring RD links every 15 minutes
    "refresh-expiring-links": {
        "task": "app.tasks.link_refresh.refresh_all_expiring_links",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    # Clean up expired links every hour
    "cleanup-expired-links": {
        "task": "app.tasks.link_refresh.cleanup_expired_links",
        "schedule": crontab(minute=0),  # Every hour at :00
    },
    # Monitor pending torrents every 5 minutes
    "monitor-pending-torrents": {
        "task": "app.tasks.torrent_check.monitor_pending_torrents",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}

# Task routes (optional - for task prioritization)
celery_app.conf.task_routes = {
    "app.tasks.link_refresh.*": {"queue": "links"},
    "app.tasks.torrent_check.*": {"queue": "torrents"},
}
