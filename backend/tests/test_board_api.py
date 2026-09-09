import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


class BoardApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_root = Path(self.temp_dir.name)

        frontend_dir = temp_root / "frontend"
        frontend_dir.mkdir(parents=True, exist_ok=True)
        (frontend_dir / "index.html").write_text("<h1>Kanban Studio</h1>", encoding="utf-8")

        self.db_path = temp_root / "pm.db"
        self.app = create_app(frontend_dir=frontend_dir, db_path=self.db_path)
        self.client_manager = TestClient(self.app)
        self.client = self.client_manager.__enter__()

    def tearDown(self) -> None:
        self.client_manager.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_get_board_seeds_default_columns(self) -> None:
        response = self.client.get("/api/users/user/board")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.db_path.exists())

        payload = response.json()
        columns = payload["board"]["columns"]
        self.assertEqual(len(columns), 5)
        self.assertEqual(
            [column["id"] for column in columns],
            [
                "col-backlog",
                "col-discovery",
                "col-progress",
                "col-review",
                "col-done",
            ],
        )

    def test_card_lifecycle_and_column_rename(self) -> None:
        rename = self.client.patch(
            "/api/users/user/columns/col-backlog",
            json={"title": "Planned Work"},
        )
        self.assertEqual(rename.status_code, 200)
        self.assertEqual(rename.json()["board"]["columns"][0]["title"], "Planned Work")

        created = self.client.post(
            "/api/users/user/columns/col-backlog/cards",
            json={"title": "New card", "details": "Card details"},
        )
        self.assertEqual(created.status_code, 200)

        backlog_cards = created.json()["board"]["columns"][0]["cards"]
        created_card_id = backlog_cards[-1]["id"]

        updated = self.client.patch(
            f"/api/users/user/cards/{created_card_id}",
            json={"title": "Updated card", "details": "Updated details"},
        )
        self.assertEqual(updated.status_code, 200)

        updated_backlog_cards = updated.json()["board"]["columns"][0]["cards"]
        updated_card = [card for card in updated_backlog_cards if card["id"] == created_card_id][0]
        self.assertEqual(updated_card["title"], "Updated card")

        moved = self.client.post(
            f"/api/users/user/cards/{created_card_id}/move",
            json={"toColumnId": "col-review", "toPosition": 0},
        )
        self.assertEqual(moved.status_code, 200)

        review_column = [
            column
            for column in moved.json()["board"]["columns"]
            if column["id"] == "col-review"
        ][0]
        self.assertEqual(review_column["cards"][0]["id"], created_card_id)

        deleted = self.client.delete(f"/api/users/user/cards/{created_card_id}")
        self.assertEqual(deleted.status_code, 200)

        all_cards = [
            card
            for column in deleted.json()["board"]["columns"]
            for card in column["cards"]
        ]
        self.assertFalse(any(card["id"] == created_card_id for card in all_cards))

    def test_validation_errors(self) -> None:
        invalid_rename = self.client.patch(
            "/api/users/user/columns/col-backlog",
            json={"title": "   "},
        )
        self.assertEqual(invalid_rename.status_code, 400)

        invalid_create = self.client.post(
            "/api/users/user/columns/col-backlog/cards",
            json={"title": "", "details": "x"},
        )
        self.assertEqual(invalid_create.status_code, 400)

        invalid_update = self.client.patch(
            "/api/users/user/cards/card-1",
            json={},
        )
        self.assertEqual(invalid_update.status_code, 400)

        invalid_move = self.client.post(
            "/api/users/user/cards/card-nope/move",
            json={"toColumnId": "col-review", "toPosition": 0},
        )
        self.assertEqual(invalid_move.status_code, 400)

    def test_not_found_errors(self) -> None:
        missing_column = self.client.patch(
            "/api/users/user/columns/col-missing",
            json={"title": "Any"},
        )
        self.assertEqual(missing_column.status_code, 404)

        missing_card = self.client.delete("/api/users/user/cards/card-99999")
        self.assertEqual(missing_card.status_code, 404)

        created = self.client.post(
            "/api/users/user/columns/col-backlog/cards",
            json={"title": "Move me", "details": ""},
        )
        created_card_id = created.json()["board"]["columns"][0]["cards"][-1]["id"]

        missing_target = self.client.post(
            f"/api/users/user/cards/{created_card_id}/move",
            json={"toColumnId": "col-missing", "toPosition": 0},
        )
        self.assertEqual(missing_target.status_code, 404)

    def test_persistence_survives_app_restart(self) -> None:
        self.client.patch(
            "/api/users/user/columns/col-backlog",
            json={"title": "Persisted Backlog"},
        )
        created = self.client.post(
            "/api/users/user/columns/col-backlog/cards",
            json={"title": "Persistent Card", "details": "Will survive restart"},
        )
        self.assertEqual(created.status_code, 200)

        second_app = create_app(frontend_dir=Path(self.temp_dir.name) / "frontend", db_path=self.db_path)
        with TestClient(second_app) as second_client:
            board = second_client.get("/api/users/user/board")
            self.assertEqual(board.status_code, 200)

            payload = board.json()
            backlog_column = payload["board"]["columns"][0]
            self.assertEqual(backlog_column["title"], "Persisted Backlog")
            self.assertTrue(
                any(card["title"] == "Persistent Card" for card in backlog_column["cards"])
            )


if __name__ == "__main__":
    unittest.main()
