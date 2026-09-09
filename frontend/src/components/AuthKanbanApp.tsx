"use client";

import { useState, type FormEvent } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import type { BoardData } from "@/lib/kanban";
import {
  createCard,
  deleteCard,
  fetchBoard,
  moveCard,
  renameColumn,
} from "@/lib/boardApi";

const VALID_USERNAME = "user";
const VALID_PASSWORD = "password";

export const AuthKanbanApp = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [authenticatedUsername, setAuthenticatedUsername] = useState<string | null>(null);
  const [board, setBoard] = useState<BoardData | null>(null);
  const [isBoardLoading, setIsBoardLoading] = useState(false);
  const [isBoardMutating, setIsBoardMutating] = useState(false);
  const [boardError, setBoardError] = useState("");

  const isAuthenticated = authenticatedUsername !== null;

  const toMessage = (value: unknown) => {
    if (value instanceof Error) {
      return value.message;
    }
    return "Unexpected error. Please retry.";
  };

  const loadBoard = async (targetUsername: string) => {
    setIsBoardLoading(true);
    setBoardError("");

    try {
      const nextBoard = await fetchBoard(targetUsername);
      setBoard(nextBoard);
    } catch (loadError) {
      setBoard(null);
      setBoardError(toMessage(loadError));
    } finally {
      setIsBoardLoading(false);
    }
  };

  const runBoardMutation = async (work: () => Promise<BoardData>) => {
    setIsBoardMutating(true);
    setBoardError("");

    try {
      const nextBoard = await work();
      setBoard(nextBoard);
    } catch (mutationError) {
      setBoardError(toMessage(mutationError));
    } finally {
      setIsBoardMutating(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedUsername = username.trim();

    if (normalizedUsername === VALID_USERNAME && password === VALID_PASSWORD) {
      setAuthenticatedUsername(normalizedUsername);
      setError("");
      setPassword("");
      await loadBoard(normalizedUsername);
      return;
    }

    setError("Invalid username or password.");
  };

  const handleLogout = () => {
    setAuthenticatedUsername(null);
    setBoard(null);
    setBoardError("");
    setUsername("");
    setPassword("");
    setError("");
  };

  if (!isAuthenticated) {
    return (
      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
        <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

        <main className="relative mx-auto flex min-h-screen max-w-[760px] items-center px-6 py-12">
          <section className="w-full rounded-[32px] border border-[var(--stroke)] bg-white/85 p-8 shadow-[var(--shadow)] backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
              Project Access
            </p>
            <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
              Sign in to continue
            </h1>
            <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
              Use the MVP credentials to open your board.
            </p>

            <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
              <div>
                <label
                  htmlFor="username"
                  className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
                >
                  Username
                </label>
                <input
                  id="username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                  autoComplete="username"
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                  autoComplete="current-password"
                  required
                />
              </div>

              {error ? (
                <p role="alert" className="text-sm font-semibold text-[var(--secondary-purple)]">
                  {error}
                </p>
              ) : null}

              <button
                type="submit"
                className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-white transition hover:brightness-110"
              >
                Sign in
              </button>

              <p className="text-xs text-[var(--gray-text)]">
                Credentials: user / password
              </p>
            </form>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="absolute right-6 top-6 z-20">
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-full border border-[var(--stroke)] bg-white/90 px-4 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-[var(--navy-dark)] shadow-[0_10px_24px_rgba(3,33,71,0.1)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
        >
          Log out
        </button>
      </div>

      {isBoardLoading && !board ? (
        <main className="relative mx-auto flex min-h-screen max-w-[760px] items-center px-6 py-12">
          <section className="w-full rounded-[32px] border border-[var(--stroke)] bg-white/85 p-8 shadow-[var(--shadow)] backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
              Loading
            </p>
            <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
              Loading your board
            </h1>
          </section>
        </main>
      ) : null}

      {boardError ? (
        <div className="relative mx-auto mt-20 max-w-[1500px] px-6" role="alert">
          <div className="rounded-2xl border border-[var(--secondary-purple)]/30 bg-white/90 px-4 py-3 text-sm text-[var(--secondary-purple)] shadow-[var(--shadow)]">
            {boardError}
            {authenticatedUsername ? (
              <button
                type="button"
                onClick={() => {
                  void loadBoard(authenticatedUsername);
                }}
                className="ml-4 rounded-full border border-[var(--secondary-purple)]/35 px-3 py-1 text-xs font-semibold uppercase tracking-[0.15em] transition hover:bg-[var(--secondary-purple)] hover:text-white"
              >
                Retry
              </button>
            ) : null}
          </div>
        </div>
      ) : null}

      {board ? (
        <KanbanBoard
          board={board}
          isMutating={isBoardMutating}
          onRenameColumn={(columnId, title) => {
            if (!authenticatedUsername) {
              return Promise.resolve();
            }
            return runBoardMutation(() => renameColumn(authenticatedUsername, columnId, title));
          }}
          onAddCard={(columnId, title, details) => {
            if (!authenticatedUsername) {
              return Promise.resolve();
            }
            return runBoardMutation(() =>
              createCard(authenticatedUsername, columnId, title, details)
            );
          }}
          onDeleteCard={(columnId, cardId) => {
            if (!authenticatedUsername) {
              return Promise.resolve();
            }
            return runBoardMutation(() => deleteCard(authenticatedUsername, cardId));
          }}
          onMoveCard={(cardId, toColumnId, toPosition) => {
            if (!authenticatedUsername) {
              return Promise.resolve();
            }
            return runBoardMutation(() =>
              moveCard(authenticatedUsername, cardId, toColumnId, toPosition)
            );
          }}
        />
      ) : null}
    </div>
  );
};