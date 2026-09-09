import type { BoardData, Card, Column } from "@/lib/kanban";

type ApiCard = {
  id: string;
  title: string;
  details: string;
  position: number;
};

type ApiColumn = {
  id: string;
  key: string;
  title: string;
  position: number;
  cards: ApiCard[];
};

type ApiBoardResponse = {
  board: {
    id: string;
    userId: string;
    username: string;
    title: string;
    columns: ApiColumn[];
  };
  meta: {
    updatedAt: string;
  };
};

const resolveApiBaseUrl = () => {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (!configuredBaseUrl) {
    return "";
  }
  return configuredBaseUrl.replace(/\/+$/, "");
};

const toBoardData = (payload: ApiBoardResponse): BoardData => {
  const cards: Record<string, Card> = {};

  const columns: Column[] = [...payload.board.columns]
    .sort((left, right) => left.position - right.position)
    .map((column) => {
      const sortedCards = [...column.cards].sort(
        (left, right) => left.position - right.position
      );

      for (const card of sortedCards) {
        cards[card.id] = {
          id: card.id,
          title: card.title,
          details: card.details,
        };
      }

      return {
        id: column.id,
        title: column.title,
        cardIds: sortedCards.map((card) => card.id),
      };
    });

  return {
    columns,
    cards,
  };
};

const parseErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (payload.detail) {
      return payload.detail;
    }
  } catch {
    // Ignore JSON parse errors and fallback to status-based message.
  }

  return `Request failed with status ${response.status}.`;
};

const requestBoard = async (path: string, init?: RequestInit): Promise<BoardData> => {
  const response = await fetch(`${resolveApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiBoardResponse;
  return toBoardData(payload);
};

export const fetchBoard = async (username: string): Promise<BoardData> => {
  return requestBoard(`/api/users/${encodeURIComponent(username)}/board`);
};

export const renameColumn = async (
  username: string,
  columnId: string,
  title: string
): Promise<BoardData> => {
  return requestBoard(
    `/api/users/${encodeURIComponent(username)}/columns/${encodeURIComponent(columnId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }
  );
};

export const createCard = async (
  username: string,
  columnId: string,
  title: string,
  details: string
): Promise<BoardData> => {
  return requestBoard(
    `/api/users/${encodeURIComponent(username)}/columns/${encodeURIComponent(columnId)}/cards`,
    {
      method: "POST",
      body: JSON.stringify({ title, details }),
    }
  );
};

export const updateCard = async (
  username: string,
  cardId: string,
  changes: { title?: string; details?: string }
): Promise<BoardData> => {
  return requestBoard(
    `/api/users/${encodeURIComponent(username)}/cards/${encodeURIComponent(cardId)}`,
    {
      method: "PATCH",
      body: JSON.stringify(changes),
    }
  );
};

export const deleteCard = async (username: string, cardId: string): Promise<BoardData> => {
  return requestBoard(
    `/api/users/${encodeURIComponent(username)}/cards/${encodeURIComponent(cardId)}`,
    {
      method: "DELETE",
    }
  );
};

export const moveCard = async (
  username: string,
  cardId: string,
  toColumnId: string,
  toPosition: number
): Promise<BoardData> => {
  return requestBoard(
    `/api/users/${encodeURIComponent(username)}/cards/${encodeURIComponent(cardId)}/move`,
    {
      method: "POST",
      body: JSON.stringify({ toColumnId, toPosition }),
    }
  );
};
