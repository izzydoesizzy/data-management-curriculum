"""
Builds the static site from content/*.html fragments.

    python3 tools/build.py

Output: index.html, toolkit.html, data.html, glossary.html, weeks/week-NN.html
Edit the fragments in content/ (or the WEEKS list below), then re-run.
"""
import html
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")

SITE_TITLE = "Data Skills for Casework"

PHASES = {
    "excel": ("Phase 1 · Excel foundations", "excel", "var(--excel)",
              "Turn a messy system export into answers: clean it, look things up, total it, pivot it."),
    "pq": ("Phase 2 · Power Query", "pq", "var(--pq)",
           "Record your cleaning steps once, then refresh them every month with one click."),
    "pbi": ("Phase 3 · Power BI", "pbi", "var(--pbi)",
            "Connect tables with relationships, write measures, and build the report you always wanted."),
    "cap": ("Phase 4 · Capstone", "cap", "var(--cap)",
            "Prove it: answer real questions with your own dashboard, then plan for real data."),
}

# (number, phase, tool label, title, one-line goal, time)
WEEKS = [
    (1, "excel", "Excel", "Set up and meet your data",
     "Get your free tools working, download the practice data and learn what a good raw table looks like.", "60 min"),
    (2, "excel", "Excel", "Tables, sorting and filtering",
     "Turn plain cells into an Excel Table and answer your first questions with sort and filter.", "60 min"),
    (3, "excel", "Excel", "Cleaning messy exports",
     "Fix the mess that real systems produce: stray spaces, inconsistent case, duplicates and blanks.", "75 min"),
    (4, "excel", "Excel", "Lookups: attach the dollar amounts",
     "Use XLOOKUP to bring each service's cost into your services table. This is where the money appears.", "60 min"),
    (5, "excel", "Excel", "Project 1: spend per client",
     "Answer the question that started all this: how much have we spent on each client?", "90 min"),
    (6, "excel", "Excel", "Project 2: PivotTables",
     "Summarize 13,000 rows in seconds by program, category and client, with clickable filters.", "90 min"),
    (7, "pq", "Power Query", "Power Query: a recipe for cleaning",
     "Redo Week 3's cleaning as recorded steps you never have to repeat by hand.", "75 min"),
    (8, "pq", "Power Query", "Merge, append and refresh",
     "Join tables inside Power Query and add next month's data without starting over.", "90 min"),
    (9, "pbi", "Power BI", "Get Power BI running on your Mac",
     "Choose your Power BI path, load the four tables and find your way around.", "75 min"),
    (10, "pbi", "Power BI", "Relationships: connect the dots",
     "Link clients, services, codes and workers so Power BI understands how they relate.", "60 min"),
    (11, "pbi", "Power BI", "Measures: your first DAX",
     "Write the three measures every casework report needs: Total Spend, Clients Served and Avg Spend per Client.", "75 min"),
    (12, "pbi", "Power BI", "Time: months, trends and length of stay",
     "Add a month column, see spending over time and calculate average length of stay.", "75 min"),
    (13, "pbi", "Power BI", "Designing a report people actually use",
     "Learn the handful of design rules that separate useful reports from terrible ones.", "60 min"),
    (14, "pbi", "Power BI", "Project 3: Casework Cost Dashboard",
     "Build a one-page dashboard to an exact spec, then use it to answer questions.", "2 × 60 min"),
    (15, "cap", "Capstone", "Capstone: answer the questions",
     "Five realistic questions from a manager. Answer each one with your dashboard.", "90 min"),
    (16, "cap", "Capstone", "Real data, safely, and what's next",
     "Plan how to get real exports at work, protect client privacy and keep growing.", "60 min"),
]

NAV = [("index.html", "Schedule"), ("caseworks.html", "Caseworks"), ("toolkit.html", "Free toolkit"),
       ("data.html", "Practice data"), ("glossary.html", "Glossary")]


def layout(title, body, root, current="", description="", week=None, wide=False):
    here = ' aria-current="page"'
    nav = "".join(
        f'<a href="{root}{href}"{here if href == current else ""}>{label}</a>'
        for href, label in NAV)
    week_attr = f' data-week="{week}"' if week else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📊</text></svg>">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body data-root="{root}"{week_attr}>
<header class="site-header">
  <div class="inner">
    <a class="brand" href="{root}index.html">📊 Data Skills <span>for Casework</span></a>
    <nav class="site-nav" aria-label="Main">{nav}</nav>
  </div>
  <div class="mini-progress" aria-hidden="true"><div></div></div>
</header>
<main{' class="wide"' if wide else ''}>
{body}
</main>
<footer class="site-footer">
  Built for Laura · All practice data is fictional · Your progress is saved in this browser only
</footer>
<script src="{root}assets/app.js"></script>
</body>
</html>
"""


def read(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
        return f.read()


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def add_task_boxes(fragment, prefix):
    """<ul class="tasks"><li>Do X</li></ul>  ->  checkbox items with stable ids."""
    counter = {"n": 0}

    def ul(m):
        def li(m2):
            counter["n"] += 1
            tid = f"{prefix}-t{counter['n']}"
            return (f'<li><label><input type="checkbox" data-task="{tid}">'
                    f'<span>{m2.group(1).strip()}</span></label></li>')
        return m.group(1) + re.sub(r"<li>(.*?)</li>", li, m.group(2), flags=re.S) + m.group(3)

    return re.sub(r'(<ul class="tasks">)(.*?)(</ul>)', ul, fragment, flags=re.S)


def week_file(n):
    return f"week-{n:02d}.html"


def build_week(i, w):
    n, phase, tool, title, goal, time = w
    phase_name, phase_cls, _, _ = PHASES[phase]
    frag = add_task_boxes(read(f"weeks/{week_file(n)}"), f"w{n:02d}")
    prev_link = (f'<a href="{week_file(WEEKS[i-1][0])}">← Week {WEEKS[i-1][0]}: {WEEKS[i-1][3]}</a>'
                 if i > 0 else '<a href="../index.html">← Schedule</a>')
    next_link = (f'<a href="{week_file(WEEKS[i+1][0])}">Week {WEEKS[i+1][0]}: {WEEKS[i+1][3]} →</a>'
                 if i + 1 < len(WEEKS) else '<a href="../index.html">Back to schedule →</a>')
    body = f"""<p class="eyebrow">Week {n} of {len(WEEKS)} · {phase_name}</p>
<h1>{title}</h1>
<div class="meta">
  <span class="pill {phase_cls}">{tool}</span>
  <span class="pill">⏱ About {time}</span>
</div>
<p class="lede">{goal}</p>
{frag}
<div class="week-done">
  <label><input type="checkbox" data-week-done="{n}"> I finished Week {n}</label>
  <p class="done-msg" hidden>Week {n} is done. Take a breath; next week builds on this.</p>
</div>
<nav class="pager" aria-label="Weeks">{prev_link}{next_link}</nav>
"""
    write(f"weeks/{week_file(n)}",
          layout(f"Week {n}: {title}", body, "../", description=goal, week=n))


def build_index():
    phases_html = []
    for key, (name, cls, color, blurb) in PHASES.items():
        items = []
        for w in WEEKS:
            if w[1] != key:
                continue
            n, _, _, title, goal, time = w
            items.append(f"""<li data-week-item="{n}"><a href="weeks/{week_file(n)}">
  <span class="num">W{n}</span>
  <span class="title">{title}</span>
  <span class="sub">{goal} · {time}</span>
  <span class="status"></span>
</a></li>""")
        phases_html.append(f"""<section class="phase">
<h2><span class="dot" style="background:{color}"></span>{name}</h2>
<p>{blurb}</p>
<ul class="week-list">
{chr(10).join(items)}
</ul>
</section>""")
    body = read("index.html").replace("{{SCHEDULE}}", "\n".join(phases_html))
    write("index.html", layout(SITE_TITLE, body, "", current="index.html",
                               description="A 16-week, 1–2 hours a week plan to build custom CaseWORKS reports and dashboards with Excel and Power BI."))


def build_page(name, title, desc):
    body = add_task_boxes(read(name), name.split(".")[0])
    write(name, layout(f"{title} · {SITE_TITLE}", body, "", current=name, description=desc))


def build_zip():
    """Bundle the practice files (fixed timestamps so the zip is reproducible)."""
    files = ["services_raw.csv", "clients.csv", "service_codes.csv", "workers.csv",
             "services_2026-09.csv", "services_clean.csv", "referrals.csv", "appointments.csv",
             "powerbi-starter.xlsx"]
    with zipfile.ZipFile(os.path.join(ROOT, "data", "practice-data.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            with open(os.path.join(ROOT, "data", f), "rb") as fh:
                info = zipfile.ZipInfo(f"Data Course/{f}", date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, fh.read())


if __name__ == "__main__":
    build_zip()
    for i, w in enumerate(WEEKS):
        build_week(i, w)
    build_index()
    build_page("caseworks.html", "Caseworks", "Using Power BI and Excel to build custom reports from CaseWORKS case-management data.")
    build_page("toolkit.html", "Free toolkit", "Free and low-cost ways to use Excel and Power BI on a Mac.")
    build_page("data.html", "Practice data", "Download the fictional casework dataset used in every week.")
    build_page("glossary.html", "Glossary", "Plain-English definitions of data terms.")
    print(f"built {len(WEEKS)} weeks + 5 pages")
