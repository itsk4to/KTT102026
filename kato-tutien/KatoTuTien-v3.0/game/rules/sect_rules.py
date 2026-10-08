from __future__ import annotations

from game.content.sects_content import SECT_PERMISSIONS, SECT_ROLES


def has_permission(role: str, perm: str) -> bool:
    return role in SECT_PERMISSIONS.get(perm, set())


def role_rank(role: str) -> int:
    """Lower rank number = greater authority."""
    try:
        return SECT_ROLES.index(role)
    except ValueError:
        return len(SECT_ROLES)


def can_manage_target(actor_role: str, target_role: str, permission: str) -> bool:
    """An actor may only manage a lower-authority member."""
    return (
        has_permission(actor_role, permission)
        and target_role in SECT_ROLES
        and actor_role in SECT_ROLES
        and role_rank(actor_role) < role_rank(target_role)
    )


def can_change_role(actor_role: str, target_role: str, new_role: str, *, promote: bool) -> bool:
    if new_role not in SECT_ROLES or target_role not in SECT_ROLES:
        return False
    permission = "sect.promote" if promote else "sect.demote"
    if not can_manage_target(actor_role, target_role, permission):
        return False
    if new_role == "Tông Chủ":
        return False
    actor_rank = role_rank(actor_role)
    target_rank = role_rank(target_role)
    new_rank = role_rank(new_role)
    if new_rank == target_rank or new_rank <= actor_rank:
        return False
    return new_rank < target_rank if promote else new_rank > target_rank


def can_kick(actor_role: str, target_role: str) -> bool:
    return can_manage_target(actor_role, target_role, "sect.kick")
