# Income and Expense Manager

A small personal-finance project for recording money received and money spent. It is designed to be straightforward to run and explain.

## Technology

- **HTML** builds the page.
- **CSS** styles the page.
- **JavaScript** reads form values, calls the API, and updates the page.
- **FastAPI** serves the page and handles API requests.
- **SQLite** stores users, categories, income, and expenses in one local file.
- **Python `sqlite3`** runs direct SQL. There is no ORM or separate database server.

## Features

- Create and switch between local user profiles. Each profile has its own income and expenses. Profiles do not have passwords and are not login accounts.
- Add, edit, search, filter, and delete income and expense records.
- Add separate categories for income and expenses. A category cannot be deleted while a saved record uses it.
- Create a report for a selected profile and optional date range. It shows income, expenses, remaining balance, and totals by category.
- Keep records in `expenses.db`, created beside the Python files when the app starts.

## Project structure

```text
sdp_project_3rdsem/
├── main.py             FastAPI page and API routes
├── database.py         SQLite connection and database setup
├── models.py           SQL table definitions
├── schemas.py          Rules for data sent to the API
├── requirements.txt    Python packages needed to run the app
├── expenses.db         Local database (created automatically)
├── README.md           Setup and feature guide
├── EXPLANATION.md      Beginner-friendly mentor walkthrough
└── public/
    ├── index.html      Page structure
    ├── style.css       Page styling
    └── app.js          Browser actions and API calls
```

## Run the app

1. Open PowerShell in this folder.
2. Install the two required Python packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Start the web app:

   ```powershell
   python -m uvicorn main:app --reload
   ```

4. Open <http://127.0.0.1:8000> in a browser.
5. To see and try the API routes, open <http://127.0.0.1:8000/docs>.

Keep the PowerShell window open while using the app. Press `Ctrl+C` in that window to stop it.

## API routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/users` | List local profiles |
| POST | `/api/users` | Add a profile |
| GET | `/api/categories` | List categories; may filter by type |
| POST | `/api/categories` | Add an income or expense category |
| DELETE | `/api/categories/{category_id}` | Delete an unused category |
| GET | `/api/entries` | List entries for a profile, with type/search/category filters |
| POST | `/api/entries?type=income` or `expense` | Add an income or expense |
| PUT | `/api/entries/{entry_id}?type=income` or `expense` | Edit an entry |
| DELETE | `/api/entries/{entry_id}?type=income&user_id=1` | Delete an entry |
| GET | `/api/reports` | Calculate income, expenses, balance, and category totals |

For a simple explanation of how each file works and how a record moves through the app, see [EXPLANATION.md](EXPLANATION.md).
# sdp_project_expense_management_system
