"""Durable prison labour sessions and idempotent community payouts."""
from __future__ import annotations

import json
import time
from typing import Any

from game.database.connection import Database


class PrisonError(ValueError):
    """Expected prison workflow validation error."""


class PrisonRepository:
    def __init__(self, db: Database):
        self.db = db

    def create_session(self, *, guild_id: str, user_id: str, actor_id: str,
                       required_stones: int, reason: str, now: int | None = None) -> dict[str, Any]:
        timestamp = int(time.time()) if now is None else int(now)
        active = self.get_active_session_for_user(str(user_id))
        if active:
            raise PrisonError("Người chơi này đang có phiên tù chưa hoàn tất.")
        try:
            cur = self.db.execute(
                """INSERT INTO prison_sessions
                   (guild_id,user_id,actor_id,required_stones,total_stones,reason,status,created_at,last_mined_at)
                   VALUES(?,?,?,?,0,?,'preparing',?,0)""",
                (str(guild_id), str(user_id), str(actor_id), int(required_stones), str(reason)[:500], timestamp),
            )
        except Exception as exc:
            # The partial unique index is the final guard against concurrent /phattu calls.
            raise PrisonError("Không thể tạo phiên tù: người chơi có thể đang có phiên chưa kết thúc.") from exc
        return self.get_session(int(cur.lastrowid))  # type: ignore[return-value]

    def get_session(self, session_id: int) -> dict[str, Any] | None:
        row = self.db.fetchone("SELECT * FROM prison_sessions WHERE session_id=?", (int(session_id),))
        return dict(row) if row is not None else None

    def get_active_session(self, guild_id: str, user_id: str) -> dict[str, Any] | None:
        row = self.db.fetchone(
            """SELECT * FROM prison_sessions WHERE guild_id=? AND user_id=?
               AND status IN ('preparing','active','release_pending') ORDER BY session_id DESC LIMIT 1""",
            (str(guild_id), str(user_id)),
        )
        return dict(row) if row is not None else None

    def get_active_session_for_user(self, user_id: str) -> dict[str, Any] | None:
        row = self.db.fetchone(
            "SELECT * FROM prison_sessions WHERE user_id=? AND status IN ('preparing','active','release_pending') ORDER BY session_id DESC LIMIT 1",
            (str(user_id),),
        )
        return dict(row) if row is not None else None

    def get_session_for_user(self, guild_id: str, user_id: str) -> dict[str, Any] | None:
        return self.get_active_session(guild_id, user_id)

    def set_permission_snapshot(self, session_id: int, snapshot: dict[str, Any]) -> None:
        self.db.execute(
            "UPDATE prison_sessions SET permission_snapshot=? WHERE session_id=? AND status='preparing'",
            (json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), int(session_id)),
        )

    def permission_snapshot(self, session: dict[str, Any]) -> dict[str, Any]:
        value = session.get("permission_snapshot") or "{}"
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    def activate(self, session_id: int) -> None:
        cur = self.db.execute(
            "UPDATE prison_sessions SET status='active' WHERE session_id=? AND status='preparing'",
            (int(session_id),),
        )
        if cur.rowcount != 1:
            raise PrisonError("Không thể xác nhận phiên tù đã được thiết lập.")

    def mark_failed(self, session_id: int, error: str) -> None:
        self.db.execute(
            "UPDATE prison_sessions SET status='failed', last_error=? WHERE session_id=? AND status='preparing'",
            (str(error)[:1000], int(session_id)),
        )

    def list_sessions(self, *statuses: str) -> list[dict[str, Any]]:
        if not statuses:
            return []
        placeholders = ",".join("?" for _ in statuses)
        rows = self.db.fetchall(
            f"SELECT * FROM prison_sessions WHERE status IN ({placeholders}) ORDER BY session_id",
            tuple(statuses),
        )
        return [dict(row) for row in rows]

    def mine(self, *, guild_id: str, user_id: str, channel_id: str,
             expected_channel_id: str, event_id: str, cooldown_seconds: int,
             now: int | None = None) -> dict[str, Any]:
        timestamp = int(time.time()) if now is None else int(now)
        if str(channel_id) != str(expected_channel_id):
            raise PrisonError("Chỉ được dùng `.kthac` trong kênh lao ngục được cấu hình.")
        with self.db.transaction():
            duplicate = self.db.fetchone(
                "SELECT 1 FROM prison_mining_events WHERE event_id=?", (str(event_id),)
            )
            if duplicate:
                raise PrisonError("Lượt khai thác này đã được ghi nhận, không thể tính hai lần.")
            row = self.db.fetchone(
                """SELECT * FROM prison_sessions WHERE guild_id=? AND user_id=? AND status='active'
                   ORDER BY session_id DESC LIMIT 1""",
                (str(guild_id), str(user_id)),
            )
            if row is None:
                raise PrisonError("Ngươi hiện không có phiên lao tù đang hoạt động.")
            session = dict(row)
            if not self.db.fetchone("SELECT 1 FROM players WHERE user_id=?", (str(user_id),)):
                raise PrisonError("Hãy đăng ký nhân vật bằng `.tutien` trước khi khai thác.")
            last = int(session.get("last_mined_at") or 0)
            remaining = max(0, int(cooldown_seconds) - (timestamp - last)) if last else 0
            if remaining > 0:
                raise PrisonError(f"Lao dịch cần hồi sức thêm **{remaining} giây** trước lượt tiếp theo.")
            total = int(session["total_stones"]) + 10
            required = int(session["required_stones"])
            status = "release_pending" if total >= required else "active"
            cur = self.db.execute(
                """UPDATE prison_sessions SET total_stones=?,last_mined_at=?,status=?
                   WHERE session_id=? AND status='active' AND last_mined_at=?""",
                (total, timestamp, status, int(session["session_id"]), last),
            )
            if cur.rowcount != 1:
                raise PrisonError("Lượt khai thác vừa bị xử lý ở nơi khác. Hãy kiểm tra lại tiến độ.")
            self.db.execute(
                "INSERT INTO prison_mining_events(event_id,session_id,amount,created_at) VALUES(?,?,10,?)",
                (str(event_id), int(session["session_id"]), timestamp),
            )
            updated = dict(session)
            updated.update(total_stones=total, last_mined_at=timestamp, status=status)
            return {
                "session": updated,
                "amount": 10,
                "total_stones": total,
                "required_stones": required,
                "remaining_stones": max(0, required - total),
                "release_due": status == "release_pending",
            }

    def request_release(self, session_id: int) -> dict[str, Any]:
        with self.db.transaction():
            session = self.get_session(session_id)
            if session is None:
                raise PrisonError("Không tìm thấy phiên tù này.")
            if session["status"] == "completed":
                return session
            if session["status"] not in ("active", "release_pending"):
                raise PrisonError("Phiên tù chưa sẵn sàng để thả hoặc đã bị hủy.")
            self.db.execute(
                "UPDATE prison_sessions SET status='release_pending' WHERE session_id=?",
                (int(session_id),),
            )
            return self.get_session(session_id)  # type: ignore[return-value]

    def get_pending_releases(self) -> list[dict[str, Any]]:
        return self.list_sessions("release_pending")

    def get_preparing_sessions(self) -> list[dict[str, Any]]:
        return self.list_sessions("preparing")

    def finalize_payout(self, session_id: int, *, now: int | None = None) -> dict[str, Any]:
        timestamp = int(time.time()) if now is None else int(now)
        with self.db.transaction():
            session = self.get_session(session_id)
            if session is None:
                raise PrisonError("Không tìm thấy phiên tù cần hoàn tất.")
            existing = self.db.fetchone(
                "SELECT * FROM prison_payouts WHERE session_id=?", (int(session_id),)
            )
            if existing is not None:
                payout = dict(existing)
                if session["status"] != "completed":
                    self.db.execute(
                        "UPDATE prison_sessions SET status='completed',payout_id=?,completed_at=? WHERE session_id=?",
                        (int(payout["payout_id"]), timestamp, int(session_id)),
                    )
                return payout
            if session["status"] != "release_pending":
                raise PrisonError("Chỉ được chia thưởng sau khi phiên tù chuyển sang trạng thái chờ thả.")

            target_id = str(session["user_id"])
            # The just-released prisoner is eligible because Discord access has
            # already been restored. Exclude every other open sentence; online
            # presence is irrelevant. A second open sentence in another guild
            # still excludes the same account.
            eligible = self.db.fetchall(
                """SELECT user_id FROM players
                   WHERE user_id NOT IN
                     (SELECT user_id FROM prison_sessions
                      WHERE status IN ('preparing','active','release_pending')
                        AND session_id<>?)
                   ORDER BY user_id""",
                (int(session_id),),
            )
            recipient_ids = [str(row["user_id"]) for row in eligible]
            total = int(session["total_stones"])
            count = len(recipient_ids)
            per_player = total // count if count else 0
            remainder = total % count if count else total
            cur = self.db.execute(
                """INSERT INTO prison_payouts
                   (session_id,guild_id,prisoner_id,total_stones,recipient_count,per_player_reward,remainder,created_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (int(session_id), str(session["guild_id"]), target_id, total, count, per_player, remainder, timestamp),
            )
            payout_id = int(cur.lastrowid)
            if per_player:
                for recipient_id in recipient_ids:
                    self.db.execute(
                        "UPDATE players SET spirit_stones=spirit_stones+? WHERE user_id=?",
                        (per_player, recipient_id),
                    )
                    self.db.execute(
                        "INSERT INTO prison_payout_items(payout_id,user_id,amount) VALUES(?,?,?)",
                        (payout_id, recipient_id, per_player),
                    )
            self.db.execute("INSERT OR IGNORE INTO community_fund(fund_id,spirit_stones) VALUES(1,0)")
            self.db.execute(
                "UPDATE community_fund SET spirit_stones=spirit_stones+? WHERE fund_id=1",
                (remainder,),
            )
            self.db.execute(
                "UPDATE prison_sessions SET status='completed',payout_id=?,completed_at=? WHERE session_id=?",
                (payout_id, timestamp, int(session_id)),
            )
            result = self.db.fetchone("SELECT * FROM prison_payouts WHERE payout_id=?", (payout_id,))
            return dict(result)

    def get_payout_items(self, payout_id: int) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            "SELECT * FROM prison_payout_items WHERE payout_id=? ORDER BY user_id", (int(payout_id),)
        )
        return [dict(row) for row in rows]

    def mark_announcement_sent(self, session_id: int, now: int | None = None) -> None:
        timestamp = int(time.time()) if now is None else int(now)
        self.db.execute(
            "UPDATE prison_sessions SET announcement_sent_at=? WHERE session_id=? AND announcement_sent_at=0",
            (timestamp, int(session_id)),
        )

    def get_unannounced_completed(self) -> list[dict[str, Any]]:
        rows = self.db.fetchall(
            "SELECT * FROM prison_sessions WHERE status='completed' AND announcement_sent_at=0 ORDER BY session_id"
        )
        return [dict(row) for row in rows]
