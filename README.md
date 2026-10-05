# Data Skills for Casework

A 16-week, 1–2 hours a week curriculum for learning **Excel, Power Query and Power BI** using a
realistic (fictional) casework dataset. It's built for a Mac user and uses only free tools.

**Live site:** https://izzydoesizzy.github.io/data-management-curriculum/

## What's inside

| Path | What it is |
|---|---|
| `index.html` | Home page: progress bar, start-date planner, 16-week schedule |
| `weeks/week-NN.html` | One page per week: Learn → Do → Checkpoint → Stuck? → Stretch |
| `toolkit.html` | Free tools, and the three Power BI options for a Mac |
| `data.html` | Practice data downloads and data dictionary |
| `glossary.html` | Plain-English definitions |
| `data/` | Practice CSVs, `powerbi-starter.xlsx`, `answer-key.json`, and the scripts that generate them |
| `content/` | **Edit these** source fragments, then rebuild |
| `assets/` | Shared CSS and JS (progress saved in `localStorage`, answer checker) |

## Editing and rebuilding

```bash
python3 data/generate.py        # regenerate data + answer key (deterministic, stdlib only)
python3 data/make_workbook.py   # rebuild powerbi-starter.xlsx (pip install openpyxl)
python3 tools/build.py          # rebuild all HTML pages + practice-data.zip
```

Preview locally with `python3 -m http.server`, then open http://localhost:8000. The answer checker
needs a web server; it won't work from `file://`.

## Publishing on GitHub Pages

Repository **Settings → Pages → Build and deployment → Source: Deploy from a branch**, choose
branch `main` and folder `/ (root)`, then Save. The site appears at the URL above within a minute or two.
