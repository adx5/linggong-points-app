"""routers 包入口"""
from . import admin, ads, auth, exchange, referral, tasks, user, verify

__all__ = [
    "auth",
    "user",
    "tasks",
    "ads",
    "verify",
    "exchange",
    "referral",
    "admin",
]
