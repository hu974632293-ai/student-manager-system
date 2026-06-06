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
        "letters",
        "weather",
        "geocode",
        "ai-chat",
        "data-query",
        "permissions",
    ],
    ROLE_TEACHER: [
        "overview",
        "students",
        "classes",
        "scores",
        "employment",
        "statistics",
        "letters",
        "weather",
        "geocode",
        "ai-chat",
    ],
    ROLE_STUDENT: [
        "overview",
        "profile",
        "scores",
        "employment",
        "weather",
        "geocode",
        "ai-chat",
    ],
    ROLE_CONSULTANT: [
        "overview",
        "students",
        "employment",
        "letters",
        "weather",
        "geocode",
        "ai-chat",
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
        "letters:send",
        "weather:use",
        "geocode:use",
        "ai-chat:use",
        "data-query:use",
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
        "letters:send",
        "weather:use",
        "geocode:use",
        "ai-chat:use",
    ],
    ROLE_STUDENT: [
        "profile:read",
        "scores:read",
        "employment:read",
        "weather:use",
        "geocode:use",
        "ai-chat:use",
    ],
    ROLE_CONSULTANT: [
        "students:read",
        "employment:read",
        "employment:write",
        "letters:send",
        "weather:use",
        "geocode:use",
        "ai-chat:use",
    ],
}


def get_modules_for_role(role: str) -> list[str]:
    return ROLE_MODULES.get(role, [])


def get_permissions_for_role(role: str) -> list[str]:
    return ROLE_PERMISSIONS.get(role, [])
