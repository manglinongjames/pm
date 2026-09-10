"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import clsx from "clsx";
import {
  closestCenter,
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { createId, initialData, moveCard, type BoardData, type Column } from "@/lib/kanban";

type KanbanBoardProps = {
  board?: BoardData;
  isMutating?: boolean;
  onRenameColumn?: (columnId: string, title: string) => Promise<void> | void;
  onAddCard?: (
    columnId: string,
    title: string,
    details: string
  ) => Promise<void> | void;
  onDeleteCard?: (columnId: string, cardId: string) => Promise<void> | void;
  onMoveCard?: (
    cardId: string,
    toColumnId: string,
    toPosition: number
  ) => Promise<void> | void;
};

const findCardLocation = (columns: Column[], cardId: string) => {
  for (const column of columns) {
    const index = column.cardIds.indexOf(cardId);
    if (index !== -1) {
      return {
        columnId: column.id,
        position: index,
      };
    }
  }

  return null;
};

export const KanbanBoard = ({
  board,
  isMutating = false,
  onRenameColumn,
  onAddCard,
  onDeleteCard,
  onMoveCard,
}: KanbanBoardProps) => {
  const [internalBoard, setInternalBoard] = useState<BoardData>(() => initialData);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [optimisticColumns, setOptimisticColumns] = useState<Column[] | null>(null);
  const lastOverId = useRef<string | null>(null);
  const currentBoard = board ?? internalBoard;
  const visibleColumns = optimisticColumns ?? currentBoard.columns;

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => currentBoard.cards, [currentBoard.cards]);

  useEffect(() => {
    setOptimisticColumns(null);
  }, [currentBoard.columns]);

  const setBoardState = (updater: (previous: BoardData) => BoardData) => {
    setInternalBoard(updater);
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const activeId = event.active.id as string;
    const overId = event.over?.id;
    if (overId && overId !== activeId) {
      lastOverId.current = overId as string;
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    const activeId = active.id as string;
    const fallbackOverId =
      lastOverId.current && lastOverId.current !== activeId
        ? lastOverId.current
        : null;
    const overId = (over?.id as string | undefined) ?? fallbackOverId;
    lastOverId.current = null;

    if (!overId || activeId === overId) {
      return;
    }

    const beforeLocation = findCardLocation(visibleColumns, activeId);
    const movedColumns = moveCard(visibleColumns, activeId, overId);
    const afterLocation = findCardLocation(movedColumns, activeId);

    if (!beforeLocation || !afterLocation) {
      return;
    }

    const unchanged =
      beforeLocation.columnId === afterLocation.columnId &&
      beforeLocation.position === afterLocation.position;

    if (unchanged) {
      return;
    }

    if (onMoveCard) {
      setOptimisticColumns(movedColumns);
      Promise.resolve(
        onMoveCard(activeId, afterLocation.columnId, afterLocation.position)
      ).finally(() => {
        setOptimisticColumns(null);
      });
      return;
    }

    setBoardState((prev) => ({
      ...prev,
      columns: movedColumns,
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    if (onRenameColumn) {
      void onRenameColumn(columnId, title);
      return;
    }

    setBoardState((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    if (onAddCard) {
      void onAddCard(columnId, title, details);
      return;
    }

    const id = createId("card");
    setBoardState((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    if (onDeleteCard) {
      void onDeleteCard(columnId, cardId);
      return;
    }

    setBoardState((prev) => {
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {visibleColumns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          <section
            className={clsx(
              "grid gap-6 lg:grid-cols-5",
              isMutating && "pointer-events-none opacity-85"
            )}
          >
            {visibleColumns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => currentBoard.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
                isBusy={isMutating}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>
    </div>
  );
};
