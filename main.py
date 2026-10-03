"""The web page and API routes for the simple money manager."""

from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import get_connection, initialize_database
from schemas import CategoryInput, EntryInput, UserInput

PUBLIC_FOLDER = Path(__file__).parent / "public"
app = FastAPI(title="Simple Income and Expense Manager")
app.mount("/static", StaticFiles(directory=PUBLIC_FOLDER), name="static")

# Create the tables and default profile before serving requests.
initialize_database()


@app.get("/")
def show_home_page():
    """Show the browser page."""
    return FileResponse(PUBLIC_FOLDER / "index.html")


@app.get("/api/users")
def get_users():
    """List the local profiles."""
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM users ORDER BY name").fetchall()
        return [dict(row) for row in rows]


@app.post("/api/users")
def add_user(user: UserInput):
    """Create a profile; profiles keep each person's records separate."""
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users (name) VALUES (?)", (user.name.strip(),)
            )
            return {"id": cursor.lastrowid, "name": user.name.strip()}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="That user already exists")


@app.get("/api/categories")
def get_categories(type: str = ""):
    """List categories, optionally for income or expense."""
    with get_connection() as connection:
        if type:
            rows = connection.execute(
                "SELECT * FROM categories WHERE type = ? ORDER BY name", (type,)
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM categories ORDER BY type, name"
            ).fetchall()
        return [dict(row) for row in rows]


@app.post("/api/categories")
def add_category(category: CategoryInput):
    """Add a category for income or expenses."""
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO categories (name, type) VALUES (?, ?)",
                (category.name.strip(), category.type),
            )
            return {"id": cursor.lastrowid, "message": "Category added"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="That category already exists")


@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int):
    """Delete a category only when no saved entry uses it."""
    with get_connection() as connection:
        category = connection.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")

        table = "incomes" if category["type"] == "income" else "expenses"
        used = connection.execute(
            f"SELECT COUNT(*) FROM {table} WHERE category = ?", (category["name"],)
        ).fetchone()[0]
        if used:
            raise HTTPException(
                status_code=400, detail="This category is used by saved entries"
            )

        connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))

    return {"message": "Category deleted"}


@app.get("/api/entries")
def get_entries(user_id: int, type: str = "expense", search: str = "", category: str = ""):
    """List one user's income or expenses with optional filters."""
    if type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="Type must be income or expense")

    table = "incomes" if type == "income" else "expenses"
    date_column = "income_date" if type == "income" else "expense_date"
    query = (
        f"SELECT id, user_id, title, amount, category, {date_column} AS entry_date, note "
        f"FROM {table} WHERE user_id = ?"
    )
    values = [user_id]

    if search:
        query += " AND (title LIKE ? OR note LIKE ?)"
        values.extend([f"%{search}%", f"%{search}%"])
    if category:
        query += " AND category = ?"
        values.append(category)
    query += f" ORDER BY {date_column} DESC, id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, values).fetchall()
        return [dict(row, type=type) for row in rows]


@app.post("/api/entries")
def add_entry(type: str, entry: EntryInput):
    """Save either an income entry or an expense entry."""
    if type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="Type must be income or expense")

    table = "incomes" if type == "income" else "expenses"
    date_column = "income_date" if type == "income" else "expense_date"

    with get_connection() as connection:
        user = connection.execute(
            "SELECT id FROM users WHERE id = ?", (entry.user_id,)
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        category = connection.execute(
            "SELECT id FROM categories WHERE name = ? AND type = ?",
            (entry.category, type),
        ).fetchone()
        if category is None:
            raise HTTPException(status_code=400, detail="Choose a valid category")

        cursor = connection.execute(
            f"INSERT INTO {table} "
            f"(user_id, title, amount, category, {date_column}, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                entry.user_id,
                entry.title.strip(),
                entry.amount,
                entry.category,
                entry.entry_date,
                entry.note.strip(),
            ),
        )
        return {"id": cursor.lastrowid, "message": "Entry added"}


@app.put("/api/entries/{entry_id}")
def update_entry(entry_id: int, type: str, entry: EntryInput):
    """Update the details of one income or expense entry."""
    if type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="Type must be income or expense")

    table = "incomes" if type == "income" else "expenses"
    date_column = "income_date" if type == "income" else "expense_date"

    with get_connection() as connection:
        user = connection.execute(
            "SELECT id FROM users WHERE id = ?", (entry.user_id,)
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        category = connection.execute(
            "SELECT id FROM categories WHERE name = ? AND type = ?",
            (entry.category, type),
        ).fetchone()
        if category is None:
            raise HTTPException(status_code=400, detail="Choose a valid category")

        cursor = connection.execute(
            f"UPDATE {table} SET user_id = ?, title = ?, amount = ?, category = ?, "
            f"{date_column} = ?, note = ? WHERE id = ? AND user_id = ?",
            (
                entry.user_id,
                entry.title.strip(),
                entry.amount,
                entry.category,
                entry.entry_date,
                entry.note.strip(),
                entry_id,
                entry.user_id,
            ),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": "Entry updated"}


@app.delete("/api/entries/{entry_id}")
def delete_entry(entry_id: int, type: str, user_id: int):
    """Delete one income or expense entry."""
    if type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="Type must be income or expense")

    table = "incomes" if type == "income" else "expenses"
    with get_connection() as connection:
        cursor = connection.execute(
            f"DELETE FROM {table} WHERE id = ? AND user_id = ?", (entry_id, user_id)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")

    return {"message": "Entry deleted"}


@app.get("/api/reports")
def get_report(user_id: int, start_date: str = "", end_date: str = ""):
    """Summarize income, expenses, balance, and category totals for one user/date range."""
    report_totals = {}
    category_totals = []
    with get_connection() as connection:
        for kind, table, date_column in (
            ("income", "incomes", "income_date"),
            ("expense", "expenses", "expense_date"),
        ):
            query = f"SELECT COALESCE(SUM(amount), 0) FROM {table} WHERE user_id = ?"
            query_values = [user_id]
            if start_date:
                query += f" AND {date_column} >= ?"
                query_values.append(start_date)
            if end_date:
                query += f" AND {date_column} <= ?"
                query_values.append(end_date)
            report_totals[kind] = connection.execute(query, query_values).fetchone()[0]

            category_query = (
                f"SELECT category, SUM(amount) AS total FROM {table} "
                "WHERE user_id = ?"
            )
            category_values = [user_id]
            if start_date:
                category_query += f" AND {date_column} >= ?"
                category_values.append(start_date)
            if end_date:
                category_query += f" AND {date_column} <= ?"
                category_values.append(end_date)
            category_query += " GROUP BY category ORDER BY total DESC"
            category_totals.extend(
                dict(row, type=kind)
                for row in connection.execute(category_query, category_values).fetchall()
            )

    income_total = report_totals["income"]
    expense_total = report_totals["expense"]
    return {
        "income_total": income_total,
        "expense_total": expense_total,
        "balance": income_total - expense_total,
        "category_totals": category_totals,
    }
