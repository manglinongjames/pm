import {
  createCard,
  deleteCard,
  fetchBoard,
  moveCard,
  renameColumn,
  updateCard,
} from "@/lib/boardApi";

describe("boardApi", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("maps API payload into UI board shape", async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          board: {
            id: "board-1",
            userId: "user-1",
            username: "user",
            title: "My Board",
            columns: [
              {
                id: "col-review",
                key: "review",
                title: "Review",
                position: 3,
                cards: [
                  {
                    id: "card-2",
                    title: "Card 2",
                    details: "Two",
                    position: 1,
                  },
                  {
                    id: "card-1",
                    title: "Card 1",
                    details: "One",
                    position: 0,
                  },
                ],
              },
              {
                id: "col-backlog",
                key: "backlog",
                title: "Backlog",
                position: 0,
                cards: [],
              },
            ],
          },
          meta: {
            updatedAt: "2026-09-08T00:00:00Z",
          },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      )
    );

    const board = await fetchBoard("user");

    expect(board.columns.map((column) => column.id)).toEqual([
      "col-backlog",
      "col-review",
    ]);
    expect(board.columns[1].cardIds).toEqual(["card-1", "card-2"]);
    expect(board.cards["card-1"].title).toBe("Card 1");
  });

  it("sends mutation payloads to the expected API endpoints", async () => {
    const payload = {
      board: {
        id: "board-1",
        userId: "user-1",
        username: "user",
        title: "My Board",
        columns: [],
      },
      meta: {
        updatedAt: "2026-09-08T00:00:00Z",
      },
    };

    fetchMock.mockImplementation(async () =>
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    await renameColumn("user", "col-backlog", "Planned Work");
    await createCard("user", "col-backlog", "New card", "Details");
    await updateCard("user", "card-1", { title: "Updated" });
    await moveCard("user", "card-1", "col-review", 0);
    await deleteCard("user", "card-1");

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      "/api/users/user/columns/col-backlog",
      expect.objectContaining({ method: "PATCH" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/users/user/columns/col-backlog/cards",
      expect.objectContaining({ method: "POST" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/users/user/cards/card-1",
      expect.objectContaining({ method: "PATCH" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      4,
      "/api/users/user/cards/card-1/move",
      expect.objectContaining({ method: "POST" })
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      5,
      "/api/users/user/cards/card-1",
      expect.objectContaining({ method: "DELETE" })
    );
  });

  it("throws API detail messages on error responses", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: "Column title cannot be empty." }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      })
    );

    await expect(renameColumn("user", "col-backlog", "")).rejects.toThrow(
      "Column title cannot be empty."
    );
  });
});
