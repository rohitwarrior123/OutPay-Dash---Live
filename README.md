# Outright Payment Dashboard — Contract / Vendor Management

Live Flask-on-Render deployment of `index.html`, with a local Windows bot that
keeps `data/dashboard_data.json` in sync with your Excel master file every 5
minutes.

## Layout
```
outright-dashboard/
├── index.html              # the dashboard (as-is from your export)
├── app.py                  # Flask server (serves index.html + /data/dashboard_data.json)
├── requirements.txt        # Flask/gunicorn deps (Render build)
├── render.yaml             # Render blueprint (optional, for one-click deploy)
├── data/
│   └── dashboard_data.json # bot-refreshed data, placeholder until first run
└── bot/
    ├── update_data.py      # reads Excel -> writes data/dashboard_data.json -> git commit/push
    ├── bot_config.json     # EDIT THIS: excel path + column mapping
    ├── requirements.txt    # pandas/openpyxl
    └── run_bot.bat         # double-click on your PC, loops every 5 min
```

## IMPORTANT — before running the bot
Open `bot/bot_config.json` and edit `column_map` so the right-hand values match
your Excel's exact column headers (case-sensitive). The `excel_path` is already
set to the path you gave me. If your sheet isn't the first tab, set
`sheet_name` to its name or index.

## Note on the dashboard itself
`index.html` currently renders from data baked into the page when it was
exported. This bot writes fresh numbers to `/data/dashboard_data.json`, but
the page needs a small `fetch('/data/dashboard_data.json')` wired into its
JS to actually display that live data instead of its original static numbers.
Send me a sample export of the Excel (or the exact column headers) and I'll
wire that fetch + table refresh into index.html in the next step.

## Deploy steps
See the terminal commands provided separately for GitHub + Render setup.
