# Mentor explanation

This guide explains what each project file does and how to describe the project. The app uses HTML, CSS, JavaScript, FastAPI, and SQLite with Python's built-in `sqlite3` library.

## 1. How the project works

```text
HTML page  ⇄  JavaScript  ⇄  FastAPI routes  ⇄  SQLite database
```

1. The browser displays `public/index.html` and applies `public/style.css`.
2. `public/app.js` reads user actions and sends HTTP requests with `fetch()`.
3. FastAPI receives those requests in `main.py` and checks submitted data with `schemas.py`.
4. The route uses `database.py` to connect to SQLite and runs a short SQL statement.
5. FastAPI returns data as JSON. JavaScript updates the page with the result.

## 2. Python files

### `models.py` — database table definitions

This file contains one SQL `CREATE TABLE` statement for each table:

- **users** stores profile IDs and names.
- **categories** stores each category name and its type (`income` or `expense`).
- **expenses** stores each expense's user ID, description, amount, category, date, and note.
- **incomes** stores the same kind of information for income records.

An ID is the unique number SQLite assigns to each row. `NOT NULL` means a value is required. `PRIMARY KEY` identifies a row. `AUTOINCREMENT` asks SQLite to choose the next ID. `UNIQUE` prevents duplicate profile names or duplicate category names of the same type.

### `database.py` — database setup and connection

- `DATABASE_FILE` builds the path to `expenses.db` beside the Python files.
- `get_connection()` opens the local SQLite file. `row_factory` lets the app read a result by its column name, such as `row["name"]`.
- `initialize_database()` runs the table definitions when the app starts.
- `INSERT OR IGNORE` adds the starter profile and categories only when they do not already exist.
- `PRAGMA table_info(expenses)` asks SQLite which columns the existing expenses table has.
- The `ALTER TABLE` statement adds `user_id` to an older version of the database. Existing expenses receive profile ID `1` (`Me`) and are kept.
- `with get_connection() as connection` groups database work together and saves successful changes when the block ends.

### `schemas.py` — API input rules

FastAPI uses these classes to check JSON before a route works with it:

- `EntryInput` describes the shared fields used for income and expenses. It requires a positive user ID and amount, and sets short maximum lengths for text.
- `UserInput` checks the profile name.
- `CategoryInput` checks the category name. `Literal["income", "expense"]` allows only those two category types.

`BaseModel` and `Field` come from Pydantic, which FastAPI uses for request validation.

### `main.py` — page and API routes

At the top, imports make FastAPI, SQLite helpers, and the input schemas available. `PUBLIC_FOLDER` points to the browser files. `app = FastAPI(...)` creates the web app, and `app.mount(...)` makes the CSS and JavaScript files available at `/static`.

`initialize_database()` runs once when this module starts. Each decorator such as `@app.get(...)` or `@app.post(...)` connects an HTTP method and URL to the function below it.

- `show_home_page()` serves `index.html` at `/`.
- `get_users()` lists the available local profiles.
- `add_user()` saves a profile name. The profiles separate records on this device; they are not accounts with passwords or authentication.
- `get_categories()` lists categories, optionally filtering by type.
- `add_category()` saves an income or expense category.
- `delete_category()` checks whether a saved entry uses the category. It returns an error instead of leaving a saved entry with an invalid category.
- `get_entries()` picks the `incomes` or `expenses` table based on the requested `type`, then filters by user, search text, and category.
- `add_entry()` checks the selected profile and category, then inserts a new income or expense row.
- `update_entry()` changes a row belonging to the selected profile. It returns a `404` response if that row does not exist for the profile.
- `delete_entry()` removes a row only when its ID and user ID match.
- `get_report()` calculates total income, total expenses, and balance for a profile. If start and end dates are provided, SQL includes only records inside that date range. It also groups totals by category.
- `HTTPException` returns a clear HTTP error when a request uses an unknown profile, category, or entry.

The table name in a query is chosen from the two fixed values `incomes` and `expenses`. User-entered values such as descriptions and amounts are passed using `?` placeholders. Placeholders keep data separate from SQL instructions.

### What the API routes mean

| Method and route | Meaning |
| --- | --- |
| `GET /api/users` | Read the profiles |
| `POST /api/users` | Create a profile |
| `GET /api/categories?type=expense` | Read categories, optionally for one type |
| `POST /api/categories` | Create a category |
| `DELETE /api/categories/{category_id}` | Delete an unused category |
| `GET /api/entries?user_id=1&type=expense` | Read a user's expenses; search and category are optional filters |
| `POST /api/entries?type=income` | Add income; use `type=expense` to add an expense |
| `PUT /api/entries/{entry_id}?type=expense` | Edit an expense; use `type=income` for income |
| `DELETE /api/entries/{entry_id}?type=income&user_id=1` | Delete a user's income row |
| `GET /api/reports?user_id=1` | Read a report; `start_date` and `end_date` are optional |

`GET` reads data, `POST` creates data, `PUT` updates data, and `DELETE` removes data.

## 3. Browser files

### `public/index.html` — content and controls

The HTML describes what appears on screen:

- The header contains the profile selector and add-user controls.
- The report cards show income, expenses, and balance.
- The date inputs select a report range.
- The entry form collects type, description, amount, date, category, and note.
- The category section adds or removes categories.
- The records section switches between income and expenses and provides search and category filters.
- Each `id` gives JavaScript a reliable name for finding a page element.
- The final `<script>` loads `app.js`; the `<link>` loads `style.css`.

### `public/style.css` — appearance

- The variables at the top define colors once so they are easy to change.
- The general rules set fonts, spacing, buttons, forms, report cards, and record rows.
- The rules under `@media` rearrange columns on small screens so the page fits a phone.
- CSS changes appearance only; the data work happens in JavaScript and Python.

### `public/app.js` — actions and page updates

- `activeUserId` remembers the selected profile. `localStorage` remembers it in this browser; it does not store the finance records.
- `editingEntryId` is `null` when adding a new row and holds an ID while editing.
- `request()` uses `fetch()` to call FastAPI, reads the JSON response, and turns an API error into a JavaScript error message.
- `startPage()` loads profiles, categories, entries, and a report when the page opens.
- `loadUsers()` fills the profile menu and keeps the current selection if it still exists.
- The add-user button sends a `POST` request, then selects the new profile.
- `loadCategories()` fills the form, category filter, and category chips using the selected entry type.
- The category buttons send `POST` to add a category and `DELETE` to remove one.
- The entry form's submit listener creates a JavaScript object from the form values and sends JSON. It uses `POST` for a new row and `PUT` for an edit.
- `loadEntries()` requests the selected user's income or expenses and displays each row. Search and category changes call it again.
- The edit button puts the row's saved values back into the form. The delete button asks for confirmation and then sends a `DELETE` request.
- `loadReport()` sends the selected profile and optional dates, then fills the income, expense, balance, and category total areas.
- `formatMoney()` formats a number as Indian rupees.
- `escapeHtml()` replaces special characters in user-entered text so the browser displays it as text instead of HTML.

## 4. Example to explain to the mentor: adding an expense

1. Choose a profile and select **Expense** in the form.
2. Enter a description, amount, date, category, and optional note.
3. JavaScript reads the form and calls `fetch("/api/entries?type=expense", ...)` with a `POST` request and JSON data.
4. FastAPI checks the JSON against `EntryInput` and calls `add_entry()`.
5. The route checks that the profile and expense category exist.
6. The route runs an `INSERT` query. `database.py` has opened the SQLite connection; SQLite saves the row to `expenses.db`.
7. FastAPI returns a small JSON response. JavaScript reloads the records and report so the new values appear.

Income follows the same steps, but uses `type=income` and the `incomes` table.

## 5. Run the project

Open PowerShell in the project folder and run:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000> for the app. Open <http://127.0.0.1:8000/docs> to try the API routes.
