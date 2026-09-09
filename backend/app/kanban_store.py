from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DEFAULT_COLUMNS = [
    ("backlog", "Backlog", 0),
    ("discovery", "Discovery", 1),
    ("progress", "In Progress", 2),
    ("review", "Review", 3),
    ("done", "Done", 4),
]


class StoreValidationError(Exception):
    pass


class StoreNotFoundError(Exception):
    pass


def initialize_database(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with _connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                title TEXT NOT NULL DEFAULT 'My Board',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                title TEXT NOT NULL,
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
                UNIQUE (board_id, key),
                UNIQUE (board_id, position)
            );

            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                column_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE,
                UNIQUE (column_id, position)
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_boards_user_id
            ON boards(user_id);

            CREATE INDEX IF NOT EXISTS idx_columns_board_id_position
            ON columns(board_id, position);

            CREATE INDEX IF NOT EXISTS idx_cards_column_id_position
            ON cards(column_id, position);

            CREATE INDEX IF NOT EXISTS idx_chat_messages_board_id_created_at
            ON chat_messages(board_id, created_at);
            """
        )


def get_board_for_user(db_path: Path, username: str) -> dict[str, Any]:
    with _connect(db_path) as connection:
        user_id, board_id = _ensure_user_and_board(connection, username)
        return _load_board_payload(connection, board_id, user_id, username)


def rename_column_for_user(
    db_path: Path, username: str, column_id: str, title: str
) -> dict[str, Any]:
    title = title.strip()
    if not title:
        raise StoreValidationError("Column title cannot be empty.")

    column_key = _parse_column_key(column_id)
    with _connect(db_path) as connection:
        user_id, board_id = _ensure_user_and_board(connection, username)

        result = connection.execute(
            """
            UPDATE columns
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE board_id = ? AND key = ?
            """,
            (title, board_id, column_key),
        )

        if result.rowcount == 0:
            raise StoreNotFoundError("Column not found for this user.")

        _touch_board(connection, board_id)
        connection.commit()
        return _load_board_payload(connection, board_id, user_id, username)


def create_card_for_user(
    db_path: Path, username: str, column_id: str, title: str, details: str
) -> dict[str, Any]:
    title = title.strip()
    details = details.strip()

    if not title:
        raise StoreValidationError("Card title cannot be empty.")

    column_key = _parse_column_key(column_id)
    with _connect(db_path) as connection:
        user_id, board_id = _ensure_user_and_board(connection, username)
        column_row = _find_column_row(connection, board_id, column_key)

        if not column_row:
            raise StoreNotFoundError("Column not found for this user.")

        column_internal_id = int(column_row["id"])

        next_position = connection.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM cards WHERE column_id = ?",
            (column_internal_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO cards (column_id, title, details, position)
            VALUES (?, ?, ?, ?)
            """,
            (column_internal_id, title, details, next_position),
        )

        _touch_board(connection, board_id)
        connection.commit()
        return _load_board_payload(connection, board_id, user_id, username)


def update_card_for_user(
    db_path: Path,
    username: str,
    card_id: str,
    title: str | None,
    details: str | None,
) -> dict[str, Any]:
    if title is None and details is None:
        raise StoreValidationError("At least one field must be provided.")

    updates: list[str] = []
    values: list[Any] = []

    if title is not None:
        normalized_title = title.strip()
        if not normalized_title:
            raise StoreValidationError("Card title cannot be empty.")
        updates.append("title = ?")
        values.append(normalized_title)

    if details is not None:
        updates.append("details = ?")
        values.append(details.strip())

    internal_card_id = _parse_card_internal_id(card_id)

    with _connect(db_path) as connection:
        user_id, board_id = _ensure_user_and_board(connection, username)

        card_row = _find_card_row(connection, board_id, internal_card_id)
        if not card_row:
            raise StoreNotFoundError("Card not found for this user.")

        query = f"UPDATE cards SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        connection.execute(query, (*values, internal_card_id))

        _touch_board(connection, board_id)
        connection.commit()
        return _load_board_payload(connection, board_id, user_id, username)


def delete_card_for_user(db_path: Path, username: str, card_id: str) -> dict[str, Any]:
    internal_card_id = _parse_card_internal_id(card_id)

    with _connect(db_path) as connection:
        user_id, board_id = _ensure_user_and_board(connection, username)

        card_row = _find_card_row(connection, board_id, internal_card_id)
        if not card_row:
            raise StoreNotFoundError("Card not found for this user.")

        column_internal_id = int(card_row["column_id"])
        previous_position = int(card_row["position"])

        connection.execute("DELETE FROM cards WHERE id = ?", (internal_card_id,))
        connection.execute(
            """
            UPDATE cards
            SET position = position - 1, updated_at = CURRENT_TIMESTAMP
            WHERE column_id = ? AND position > ?
            """,
            (column_internal_id, previous_position),
        )

        _touch_board(connection, board_id)
        connection.commit()
        return _load_board_payload(connection, board_id, user_id, username)


def move_card_for_user(
    db_path: Path,
    username: str,
    card_id: str,
    to_column_id: str,
    to_position: int | None,
) -> dict[str, Any]:
    internal_card_id = _parse_card_internal_id(card_id)
    target_column_key = _parse_column_key(to_column_id)

    with _connect(db_path) as connection:
        user_id, board_id = _ensure_user_and_board(connection, username)

        target_column = _find_column_row(connection, board_id, target_column_key)
        if not target_column:
            raise StoreNotFoundError("Target column not found for this user.")

        card_row = _find_card_row(connection, board_id, internal_card_id)
        if not card_row:
            raise StoreNotFoundError("Card not found for this user.")

        source_column_id = int(card_row["column_id"])
        source_position = int(card_row["position"])
        target_column_id = int(target_column["id"])

        if source_column_id == target_column_id:
            _move_inside_column(
                connection, source_column_id, internal_card_id, source_position, to_position
            )
        else:
            _move_across_columns(
                connection,
                source_column_id,
                target_column_id,
                internal_card_id,
                source_position,
                to_position,
            )

        _touch_board(connection, board_id)
        connection.commit()
        return _load_board_payload(connection, board_id, user_id, username)


@contextmanager
def _connect(db_path: Path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
    finally:
        connection.close()


def _ensure_user_and_board(connection: sqlite3.Connection, username: str) -> tuple[int, int]:
    username = username.strip()
    if not username:
        raise StoreValidationError("Username cannot be empty.")

    user_row = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if user_row is None:
        connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, "mvp-placeholder"),
        )
        user_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])
    else:
        user_id = int(user_row["id"])

    board_row = connection.execute(
        "SELECT id FROM boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    if board_row is None:
        connection.execute(
            "INSERT INTO boards (user_id, title) VALUES (?, ?)",
            (user_id, "My Board"),
        )
        board_id = int(connection.execute("SELECT last_insert_rowid()").fetchone()[0])

        for key, title, position in DEFAULT_COLUMNS:
            connection.execute(
                "INSERT INTO columns (board_id, key, title, position) VALUES (?, ?, ?, ?)",
                (board_id, key, title, position),
            )

        connection.commit()
    else:
        board_id = int(board_row["id"])

    return user_id, board_id


def _load_board_payload(
    connection: sqlite3.Connection, board_id: int, user_id: int, username: str
) -> dict[str, Any]:
    board_row = connection.execute(
        "SELECT id, title, updated_at FROM boards WHERE id = ?",
        (board_id,),
    ).fetchone()

    column_rows = connection.execute(
        "SELECT id, key, title, position FROM columns WHERE board_id = ? ORDER BY position ASC",
        (board_id,),
    ).fetchall()

    cards_by_column: dict[int, list[dict[str, Any]]] = {}
    for row in connection.execute(
        """
        SELECT id, column_id, title, details, position
        FROM cards
        WHERE column_id IN (SELECT id FROM columns WHERE board_id = ?)
        ORDER BY column_id ASC, position ASC
        """,
        (board_id,),
    ).fetchall():
        column_id = int(row["column_id"])
        cards_by_column.setdefault(column_id, []).append(
            {
                "id": f"card-{int(row['id'])}",
                "title": row["title"],
                "details": row["details"],
                "position": int(row["position"]),
            }
        )

    columns_payload = []
    for column in column_rows:
        column_internal_id = int(column["id"])
        column_key = str(column["key"])
        columns_payload.append(
            {
                "id": f"col-{column_key}",
                "key": column_key,
                "title": column["title"],
                "position": int(column["position"]),
                "cards": cards_by_column.get(column_internal_id, []),
            }
        )

    return {
        "board": {
            "id": f"board-{board_id}",
            "userId": f"user-{user_id}",
            "username": username,
            "title": board_row["title"],
            "columns": columns_payload,
        },
        "meta": {
            "updatedAt": board_row["updated_at"],
        },
    }


def _parse_column_key(column_id: str) -> str:
    value = column_id.strip()
    if not value:
        raise StoreValidationError("Column id cannot be empty.")

    if value.startswith("col-"):
        value = value.removeprefix("col-")

    if not value:
        raise StoreValidationError("Column id is invalid.")

    return value


def _parse_card_internal_id(card_id: str) -> int:
    value = card_id.strip()
    if value.startswith("card-"):
        value = value.removeprefix("card-")

    try:
        parsed = int(value)
    except ValueError as exc:
        raise StoreValidationError("Card id is invalid.") from exc

    if parsed <= 0:
        raise StoreValidationError("Card id is invalid.")

    return parsed


def _find_column_row(
    connection: sqlite3.Connection, board_id: int, column_key: str
) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT id, board_id, key, title, position FROM columns WHERE board_id = ? AND key = ?",
        (board_id, column_key),
    ).fetchone()


def _find_card_row(
    connection: sqlite3.Connection, board_id: int, card_id: int
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT cards.id, cards.column_id, cards.position
        FROM cards
        INNER JOIN columns ON columns.id = cards.column_id
        WHERE cards.id = ? AND columns.board_id = ?
        """,
        (card_id, board_id),
    ).fetchone()


def _touch_board(connection: sqlite3.Connection, board_id: int) -> None:
    connection.execute(
        "UPDATE boards SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (board_id,),
    )


def _move_inside_column(
    connection: sqlite3.Connection,
    column_id: int,
    card_id: int,
    source_position: int,
    target_position: int | None,
) -> None:
    max_position = int(
        connection.execute(
            "SELECT COALESCE(MAX(position), 0) FROM cards WHERE column_id = ?",
            (column_id,),
        ).fetchone()[0]
    )

    if target_position is None:
        target_position = max_position

    target_position = max(0, min(target_position, max_position))
    if target_position == source_position:
        return

    if target_position > source_position:
        connection.execute(
            """
            UPDATE cards
            SET position = position - 1, updated_at = CURRENT_TIMESTAMP
            WHERE column_id = ? AND position > ? AND position <= ?
            """,
            (column_id, source_position, target_position),
        )
    else:
        connection.execute(
            """
            UPDATE cards
            SET position = position + 1, updated_at = CURRENT_TIMESTAMP
            WHERE column_id = ? AND position >= ? AND position < ?
            """,
            (column_id, target_position, source_position),
        )

    connection.execute(
        "UPDATE cards SET position = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (target_position, card_id),
    )


def _move_across_columns(
    connection: sqlite3.Connection,
    source_column_id: int,
    target_column_id: int,
    card_id: int,
    source_position: int,
    target_position: int | None,
) -> None:
    target_count = int(
        connection.execute(
            "SELECT COUNT(*) FROM cards WHERE column_id = ?",
            (target_column_id,),
        ).fetchone()[0]
    )

    if target_position is None:
        target_position = target_count

    target_position = max(0, min(target_position, target_count))

    connection.execute(
        """
        UPDATE cards
        SET position = position - 1, updated_at = CURRENT_TIMESTAMP
        WHERE column_id = ? AND position > ?
        """,
        (source_column_id, source_position),
    )

    connection.execute(
        """
        UPDATE cards
        SET position = position + 1, updated_at = CURRENT_TIMESTAMP
        WHERE column_id = ? AND position >= ?
        """,
        (target_column_id, target_position),
    )

    connection.execute(
        """
        UPDATE cards
        SET column_id = ?, position = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (target_column_id, target_position, card_id),
    )
