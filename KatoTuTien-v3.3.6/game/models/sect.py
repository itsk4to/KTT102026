from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Sect:
    sect_id: str
    name: str
    description: str = ""
    owner_id: str = ""
    level: int = 1
    exp: int = 0
    treasury: int = 0
    linh_mach_level: int = 0
    created_at: int = 0

    @classmethod
    def from_row(cls, row) -> "Sect":
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})  # type: ignore


@dataclass
class SectMember:
    sect_id: str
    user_id: str
    role: str = "Ngoại Môn Đệ Tử"
    contribution: int = 0
    joined_at: int = 0

    @classmethod
    def from_row(cls, row) -> "SectMember":
        return cls(**{k: row[k] for k in cls.__dataclass_fields__ if k in row.keys()})  # type: ignore
