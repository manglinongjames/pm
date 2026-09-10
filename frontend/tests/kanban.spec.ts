import { expect, test, type Page } from "@playwright/test";

type MockCard = {
  id: string;
  title: string;
  details: string;
  position: number;
};

type MockColumn = {
  id: string;
  key: string;
  title: string;
  position: number;
  cards: MockCard[];
};

type MockBoard = {
  id: string;
  userId: string;
  username: string;
  title: string;
  columns: MockColumn[];
};

const createBoard = (): MockBoard => ({
  id: "board-1",
  userId: "user-1",
  username: "user",
  title: "My Board",
  columns: [
    {
      id: "col-backlog",
      key: "backlog",
      title: "Backlog",
      position: 0,
      cards: [
        {
          id: "card-1",
          title: "Card 1",
          details: "Initial card",
          position: 0,
        },
      ],
    },
    { id: "col-discovery", key: "discovery", title: "Discovery", position: 1, cards: [] },
    { id: "col-progress", key: "progress", title: "In Progress", position: 2, cards: [] },
    { id: "col-review", key: "review", title: "Review", position: 3, cards: [] },
    { id: "col-done", key: "done", title: "Done", position: 4, cards: [] },
  ],
});

const boardPayload = (board: MockBoard) => ({
  board,
  meta: {
    updatedAt: new Date().toISOString(),
  },
});

const reindexCards = (column: MockColumn) => {
  column.cards = column.cards.map((card, index) => ({ ...card, position: index }));
};

const setupMockApi = async (page: Page) => {
  let board = createBoard();
  let nextCardNumber = 2;

  await page.route("**/api/users/user/**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const path = url.pathname;

    if (method === "GET" && path === "/api/users/user/board") {
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(boardPayload(board)),
      });
      return;
    }

    const renameMatch = path.match(/^\/api\/users\/user\/columns\/(col-[^/]+)$/);
    if (method === "PATCH" && renameMatch) {
      const body = request.postDataJSON() as { title: string };
      board = {
        ...board,
        columns: board.columns.map((column) =>
          column.id === renameMatch[1] ? { ...column, title: body.title } : column
        ),
      };
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(boardPayload(board)),
      });
      return;
    }

    const createMatch = path.match(/^\/api\/users\/user\/columns\/(col-[^/]+)\/cards$/);
    if (method === "POST" && createMatch) {
      const body = request.postDataJSON() as { title: string; details: string };
      const nextCardId = `card-${nextCardNumber}`;
      nextCardNumber += 1;

      board = {
        ...board,
        columns: board.columns.map((column) => {
          if (column.id !== createMatch[1]) {
            return column;
          }
          const nextCards = [...column.cards, {
            id: nextCardId,
            title: body.title,
            details: body.details,
            position: column.cards.length,
          }];
          return {
            ...column,
            cards: nextCards,
          };
        }),
      };

      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(boardPayload(board)),
      });
      return;
    }

    const deleteMatch = path.match(/^\/api\/users\/user\/cards\/(card-[^/]+)$/);
    if (method === "DELETE" && deleteMatch) {
      const cardId = deleteMatch[1];
      board = {
        ...board,
        columns: board.columns.map((column) => {
          const nextCards = column.cards.filter((card) => card.id !== cardId);
          if (nextCards.length === column.cards.length) {
            return column;
          }
          const nextColumn = { ...column, cards: nextCards };
          reindexCards(nextColumn);
          return nextColumn;
        }),
      };

      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(boardPayload(board)),
      });
      return;
    }

    const moveMatch = path.match(/^\/api\/users\/user\/cards\/(card-[^/]+)\/move$/);
    if (method === "POST" && moveMatch) {
      const cardId = moveMatch[1];
      const body = request.postDataJSON() as { toColumnId: string; toPosition: number };

      let movedCard: MockCard | null = null;

      const withoutCard = board.columns.map((column) => {
        const index = column.cards.findIndex((card) => card.id === cardId);
        if (index === -1) {
          return column;
        }

        movedCard = column.cards[index];
        const nextCards = [...column.cards];
        nextCards.splice(index, 1);
        const nextColumn = { ...column, cards: nextCards };
        reindexCards(nextColumn);
        return nextColumn;
      });

      if (movedCard) {
        board = {
          ...board,
          columns: withoutCard.map((column) => {
            if (column.id !== body.toColumnId) {
              return column;
            }

            const insertPosition = Math.max(0, Math.min(body.toPosition, column.cards.length));
            const nextCards = [...column.cards];
            nextCards.splice(insertPosition, 0, movedCard as MockCard);
            const nextColumn = { ...column, cards: nextCards };
            reindexCards(nextColumn);
            return nextColumn;
          }),
        };
      }

      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(boardPayload(board)),
      });
      return;
    }

    await route.fulfill({
      status: 404,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ detail: "Route not mocked." }),
    });
  });
};

const login = async (page: Page, navigate = true) => {
  if (navigate) {
    await page.goto("/");
  }
  await expect(page.getByRole("heading", { name: /sign in to continue/i })).toBeVisible();
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
};

const dragCardToColumn = async (
  page: Page,
  cardTestId: string,
  columnTestId: string
) => {
  const card = page.getByTestId(cardTestId);
  const column = page.getByTestId(columnTestId);

  const cardBox = await card.boundingBox();
  const columnBox = await column.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 110,
    { steps: 18 }
  );
  await page.mouse.up();
};

test("logs in, loads the kanban board, and logs out", async ({ page }) => {
  await setupMockApi(page);
  await login(page);

  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);

  const firstColumnTitle = page.getByLabel("Column title").first();
  await firstColumnTitle.fill("Sprint Backlog");
  await firstColumnTitle.press("Tab");
  await expect(firstColumnTitle).toHaveValue("Sprint Backlog");

  await page.reload();
  await login(page, false);
  await expect(page.getByLabel("Column title").first()).toHaveValue("Sprint Backlog");

  await page.getByRole("button", { name: /log out/i }).click();
  await expect(page.getByRole("heading", { name: /sign in to continue/i })).toBeVisible();
});

test("adds a card and keeps it after reload", async ({ page }) => {
  await setupMockApi(page);
  await login(page);

  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();

  await page.reload();
  await login(page, false);
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await setupMockApi(page);
  await login(page);
  const targetColumn = page.getByTestId("column-col-review");
  await dragCardToColumn(page, "card-card-1", "column-col-review");
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();

  await page.reload();
  await login(page, false);
  await expect(page.getByTestId("column-col-review").getByTestId("card-card-1")).toBeVisible();
});

test("keeps drag-and-drop reliable across repeated moves", async ({ page }) => {
  await setupMockApi(page);
  await login(page);

  const reviewColumn = page.getByTestId("column-col-review");
  const backlogColumn = page.getByTestId("column-col-backlog");

  for (let index = 0; index < 12; index += 1) {
    await dragCardToColumn(page, "card-card-1", "column-col-review");
    await expect(reviewColumn.getByTestId("card-card-1")).toBeVisible();

    await dragCardToColumn(page, "card-card-1", "column-col-backlog");
    await expect(backlogColumn.getByTestId("card-card-1")).toBeVisible();
  }
});
