#!/usr/bin/env python3
"""
Cron-friendly sweeper that re-evaluates pending users and auto-approves
low-risk verified accounts based on the risk policy.
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timezone, timedelta

from main import app
from models import db, User


def sweep_pending_users(max_age_days: int = 7) -> int:
    approved = 0
    with app.app_context():
        try:
            from routes.utils.risk_policy import should_auto_approve
        except Exception:
            def should_auto_approve(_user):
                return False

        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)

        pending = User.query.filter(
            User.is_active == False,
            User.verified == True,
            User.created_at <= cutoff
        ).all()

        for user in pending:
            if should_auto_approve(user):
                user.is_active = True
                approved += 1

        if approved:
            db.session.commit()

    return approved


def main():
    approved = sweep_pending_users()
    print(f"Approved {approved} pending verified user(s)")


if __name__ == "__main__":
    main()


