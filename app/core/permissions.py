from __future__ import annotations


ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"
ROLE_CONSULTANT = "consultant"

ALL_ROLES = (ROLE_ADMIN, ROLE_TEACHER, ROLE_STUDENT, ROLE_CONSULTANT)

ROLE_MODULES: dict[str, list[str]] = {
    ROLE_ADMIN: [
        "overview",
        "students",
        "classes",
        "teachers",
        "scores",
        "employment",
        "statistics",
        "logs",
        "ai-chat",
        "data-query",
        "knowledge-base",
        "agents",
        "permissions",
    ],
    ROLE_TEACHER: [
        "overview",
        "students",
        "classes",
        "scores",
        "employment",
        "statistics",
        "ai-chat",
        "knowledge-base",
        "agents",
    ],
    ROLE_STUDENT: [
        "overview",
        "profile",
        "scores",
        "employment",
        "ai-chat",
        "knowledge-base",
        "agents",
    ],
    ROLE_CONSULTANT: [
        "overview",
        "students",
        "employment",
        "ai-chat",
        "knowledge-base",
    ],
}

ROLE_PERMISSIONS: dict[str, list[str]] = {
    ROLE_ADMIN: [
        "students:read",
        "students:write",
        "classes:read",
        "classes:write",
        "teachers:read",
        "teachers:write",
        "scores:read",
        "scores:write",
        "employment:read",
        "employment:write",
        "statistics:read",
        "logs:read",
        "ai-chat:use",
        "data-query:use",
        "knowledge-base:use",
        "knowledge-base:manage",
        "agents:use",
        "permissions:manage",
    ],
    ROLE_TEACHER: [
        "students:read",
        "classes:read",
        "teachers:read",
        "scores:read",
        "scores:write",
        "employment:read",
        "employment:write",
        "statistics:read",
        "ai-chat:use",
        "knowledge-base:use",
        "agents:use",
    ],
    ROLE_STUDENT: [
        "profile:read",
        "scores:read",
        "employment:read",
        "ai-chat:use",
        "knowledge-base:use",
        "agents:use",
    ],
    ROLE_CONSULTANT: [
        "students:read",
        "employment:read",
        "employment:write",
        "ai-chat:use",
        "knowledge-base:use",
    ],
}


def get_modules_for_role(role: str) -> list[str]:
    return ROLE_MODULES.get(role, [])


def get_permissions_for_role(role: str) -> list[str]:
    return ROLE_PERMISSIONS.get(role, [])
