import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthKanbanApp } from "@/components/AuthKanbanApp";
import type { BoardData } from "@/lib/kanban";
import {
  createCard,
  deleteCard,
  fetchBoard,
  moveCard,
  renameColumn,
} from "@/lib/boardApi";

vi.mock("@/lib/boardApi", () => ({
  fetchBoard: vi.fn(),
  renameColumn: vi.fn(),
  createCard: vi.fn(),
  deleteCard: vi.fn(),
  moveCard: vi.fn(),
}));

const cloneBoard = (board: BoardData): BoardData => ({
  columns: board.columns.map((column) => ({
    ...column,
    cardIds: [...column.cardIds],
  })),
  cards: Object.fromEntries(
    Object.entries(board.cards).map(([id, card]) => [id, { ...card }])
  ),
});

const createBoard = (): BoardData => ({
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1"] },
    { id: "col-discovery", title: "Discovery", cardIds: [] },
    { id: "col-progress", title: "In Progress", cardIds: [] },
    { id: "col-review", title: "Review", cardIds: [] },
    { id: "col-done", title: "Done", cardIds: [] },
  ],
  cards: {
    "card-1": {
      id: "card-1",
      title: "Seed card",
      details: "Initial card",
    },
  },
});

const fetchBoardMock = vi.mocked(fetchBoard);
const renameColumnMock = vi.mocked(renameColumn);
const createCardMock = vi.mocked(createCard);
const deleteCardMock = vi.mocked(deleteCard);
const moveCardMock = vi.mocked(moveCard);

const login = async () => {
  await userEvent.type(screen.getByLabelText(/username/i), "user");
  await userEvent.type(screen.getByLabelText(/password/i), "password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

beforeEach(() => {
  const board = createBoard();

  vi.clearAllMocks();
  fetchBoardMock.mockResolvedValue(cloneBoard(board));
  renameColumnMock.mockResolvedValue(cloneBoard(board));
  createCardMock.mockResolvedValue(cloneBoard(board));
  deleteCardMock.mockResolvedValue(cloneBoard(board));
  moveCardMock.mockResolvedValue(cloneBoard(board));
});

describe("AuthKanbanApp", () => {
  it("requires sign in before showing the kanban board", () => {
    render(<AuthKanbanApp />);

    expect(
      screen.getByRole("heading", { name: /sign in to continue/i })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Kanban Studio" })
    ).not.toBeInTheDocument();
  });

  it("rejects invalid credentials", async () => {
    render(<AuthKanbanApp />);

    await userEvent.type(screen.getByLabelText(/username/i), "wrong");
    await userEvent.type(screen.getByLabelText(/password/i), "creds");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Invalid username or password."
    );
    expect(
      screen.queryByRole("heading", { name: "Kanban Studio" })
    ).not.toBeInTheDocument();
  });

  it("allows login and logout with MVP credentials", async () => {
    render(<AuthKanbanApp />);

    await login();

    expect(
      screen.getByRole("heading", { name: "Kanban Studio" })
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    expect(
      screen.getByRole("heading", { name: /sign in to continue/i })
    ).toBeInTheDocument();
  });

  it("shows backend errors and supports retry", async () => {
    fetchBoardMock
      .mockRejectedValueOnce(new Error("Backend unavailable."))
      .mockResolvedValueOnce(createBoard());

    render(<AuthKanbanApp />);

    await login();

    expect(await screen.findByRole("alert")).toHaveTextContent("Backend unavailable.");

    await userEvent.click(screen.getByRole("button", { name: /retry/i }));

    expect(
      await screen.findByRole("heading", { name: "Kanban Studio" })
    ).toBeInTheDocument();
  });

  it("keeps board edits after logout and login", async () => {
    let board = createBoard();

    fetchBoardMock.mockImplementation(async () => cloneBoard(board));
    renameColumnMock.mockImplementation(async (_username, columnId, title) => {
      board = {
        ...board,
        columns: board.columns.map((column) =>
          column.id === columnId ? { ...column, title } : column
        ),
      };
      return cloneBoard(board);
    });

    render(<AuthKanbanApp />);

    await login();

    const firstColumnTitle = screen.getAllByLabelText("Column title")[0];
    await userEvent.clear(firstColumnTitle);
    await userEvent.type(firstColumnTitle, "Planned Work");
    await userEvent.tab();

    expect(renameColumnMock).toHaveBeenCalledWith("user", "col-backlog", "Planned Work");

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    await login();

    const firstColumnTitleAfterRelogin = await screen.findAllByLabelText("Column title");
    expect(firstColumnTitleAfterRelogin[0]).toHaveValue("Planned Work");
  });

  it("creates and deletes cards through backend mutations", async () => {
    let board = createBoard();

    fetchBoardMock.mockImplementation(async () => cloneBoard(board));
    createCardMock.mockImplementation(async (_username, columnId, title, details) => {
      const newCardId = "card-2";
      board = {
        ...board,
        cards: {
          ...board.cards,
          [newCardId]: {
            id: newCardId,
            title,
            details,
          },
        },
        columns: board.columns.map((column) =>
          column.id === columnId
            ? { ...column, cardIds: [...column.cardIds, newCardId] }
            : column
        ),
      };
      return cloneBoard(board);
    });
    deleteCardMock.mockImplementation(async (_username, cardId) => {
      board = {
        ...board,
        cards: Object.fromEntries(
          Object.entries(board.cards).filter(([id]) => id !== cardId)
        ),
        columns: board.columns.map((column) => ({
          ...column,
          cardIds: column.cardIds.filter((id) => id !== cardId),
        })),
      };
      return cloneBoard(board);
    });

    render(<AuthKanbanApp />);
    await login();

    const backlogColumn = screen.getByTestId("column-col-backlog");
    await userEvent.click(within(backlogColumn).getByRole("button", { name: /add a card/i }));
    await userEvent.type(within(backlogColumn).getByPlaceholderText("Card title"), "API card");
    await userEvent.type(within(backlogColumn).getByPlaceholderText("Details"), "From test");
    await userEvent.click(within(backlogColumn).getByRole("button", { name: /add card/i }));

    expect(createCardMock).toHaveBeenCalledWith(
      "user",
      "col-backlog",
      "API card",
      "From test"
    );
    expect(await screen.findByText("API card")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /delete api card/i }));

    expect(deleteCardMock).toHaveBeenCalledWith("user", "card-2");
    expect(screen.queryByText("API card")).not.toBeInTheDocument();
  });
});