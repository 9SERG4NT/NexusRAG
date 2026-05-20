"""
Role-Based Access Control: enforces document-level permissions at retrieval time.
"""

import json
from pathlib import Path


class RBACGuard:
    def __init__(self, users_path: Path, roles_path: Path):
        with open(users_path) as f:
            self._users: dict[str, str] = json.load(f)
        with open(roles_path) as f:
            self._roles: dict[str, dict] = json.load(f)

    def get_user_role(self, username: str) -> str | None:
        return self._users.get(username)

    def get_allowed_departments(self, username: str) -> list[str] | None:
        """Returns list of allowed department tags, or None if user unknown."""
        role = self.get_user_role(username)
        if role is None:
            return None
        return self._roles.get(role, {}).get("can_access", [])

    def is_admin(self, username: str) -> bool:
        return self.get_user_role(username) == "admin"

    def can_access_department(self, username: str, department: str) -> bool:
        allowed = self.get_allowed_departments(username)
        if allowed is None:
            return False
        return department in allowed

    def filter_chunks(self, chunks: list[dict], username: str) -> list[dict]:
        """Post-retrieval RBAC safety filter — belt-and-suspenders."""
        allowed = self.get_allowed_departments(username)
        if allowed is None:
            return []
        return [c for c in chunks if c["metadata"].get("department") in allowed]

    def check_query_access(self, username: str, query: str) -> tuple[bool, str]:
        """
        Heuristic guard: block queries whose keywords clearly target departments
        the user cannot access.  Returns (allowed, reason).
        """
        role = self.get_user_role(username)
        if role is None:
            return False, f"Unknown user '{username}'"

        allowed = self.get_allowed_departments(username)

        KEYWORD_DEPT_MAP = {
            "salary": "employees",
            "revenue": "finance",
            "budget": "finance",
            "financial": "finance",
            "incident": "incidents",
            "log": "logs",
            "error": "logs",
            "alert": "logs",
            "payroll": "employees",
        }

        q_lower = query.lower()
        for kw, dept in KEYWORD_DEPT_MAP.items():
            if kw in q_lower and dept not in allowed:
                return (
                    False,
                    f"Access denied: your role '{role}' does not permit queries about '{dept}' data.",
                )
        return True, "ok"
