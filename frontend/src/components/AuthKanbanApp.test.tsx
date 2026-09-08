import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthKanbanApp } from "@/components/AuthKanbanApp";

const login = async () => {
  await userEvent.type(screen.getByLabelText(/username/i), "user");
  await userEvent.type(screen.getByLabelText(/password/i), "password");
  await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
};

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

  it("keeps board edits after logout and login", async () => {
    render(<AuthKanbanApp />);

    await login();

    const firstColumnTitle = screen.getAllByLabelText("Column title")[0];
    await userEvent.clear(firstColumnTitle);
    await userEvent.type(firstColumnTitle, "Planned Work");
    expect(firstColumnTitle).toHaveValue("Planned Work");

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    await login();

    const firstColumnTitleAfterRelogin = screen.getAllByLabelText("Column title")[0];
    expect(firstColumnTitleAfterRelogin).toHaveValue("Planned Work");
  });
});