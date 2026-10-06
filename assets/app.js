/* Progress tracking + answer checking. Everything is stored in this browser only. */
(function () {
  "use strict";

  var TOTAL_WEEKS = 16;
  var STORE_KEY = "laura-data-curriculum-v1";
  var root = document.body.getAttribute("data-root") || "";

  // ---------- storage (never let a blocked storage break the page) ----------
  function load() {
    try {
      var raw = window.localStorage.getItem(STORE_KEY);
      var s = raw ? JSON.parse(raw) : {};
      s.tasks = s.tasks || {};
      s.weeks = s.weeks || {};
      s.answers = s.answers || {};
      return s;
    } catch (e) {
      return { tasks: {}, weeks: {}, answers: {} };
    }
  }
  var state = load();
  function save() {
    try { window.localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
  }

  function weeksDone() {
    var n = 0;
    for (var i = 1; i <= TOTAL_WEEKS; i++) if (state.weeks[i]) n++;
    return n;
  }
  function nextWeek() {
    for (var i = 1; i <= TOTAL_WEEKS; i++) if (!state.weeks[i]) return i;
    return null;
  }
  function pad(n) { return n < 10 ? "0" + n : "" + n; }

  // ---------- tool path: "ms" (Excel & Power BI) or "google" (Sheets & Looker Studio) ----------
  function paintPath() {
    var p = state.path === "google" ? "google" : "ms";
    if (p === "google") document.documentElement.setAttribute("data-path-choice", "google");
    else document.documentElement.removeAttribute("data-path-choice");
    document.querySelectorAll("[data-set-path]").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-set-path") === p ? "true" : "false");
    });
  }
  document.querySelectorAll("[data-set-path]").forEach(function (b) {
    b.addEventListener("click", function () {
      state.path = b.getAttribute("data-set-path");
      save(); paintPath();
    });
  });
  paintPath();

  // ---------- header mini progress ----------
  function paintMini() {
    var bar = document.querySelector(".mini-progress > div");
    if (bar) bar.style.width = (100 * weeksDone() / TOTAL_WEEKS) + "%";
  }

  // ---------- task checkboxes ----------
  document.querySelectorAll("input[data-task]").forEach(function (box) {
    var id = box.getAttribute("data-task");
    box.checked = !!state.tasks[id];
    box.addEventListener("change", function () {
      if (box.checked) state.tasks[id] = true; else delete state.tasks[id];
      save();
    });
  });

  // ---------- week complete ----------
  var doneBox = document.querySelector("input[data-week-done]");
  if (doneBox) {
    var wk = doneBox.getAttribute("data-week-done");
    var wrap = doneBox.closest(".week-done");
    var msg = wrap.querySelector(".done-msg");
    function paintDone() {
      doneBox.checked = !!state.weeks[wk];
      wrap.classList.toggle("is-done", doneBox.checked);
      if (msg) msg.hidden = !doneBox.checked;
    }
    paintDone();
    doneBox.addEventListener("change", function () {
      if (doneBox.checked) state.weeks[wk] = new Date().toISOString().slice(0, 10);
      else delete state.weeks[wk];
      save(); paintDone(); paintMini();
    });
  }

  // ---------- home page: progress, schedule dates, statuses ----------
  function paintHome() {
    var done = weeksDone();
    var fill = document.querySelector("[data-progress-fill]");
    if (fill) fill.style.width = (100 * done / TOTAL_WEEKS) + "%";
    var txt = document.querySelector("[data-progress-text]");
    if (txt) txt.textContent = done + " of " + TOTAL_WEEKS + " weeks complete";
    var nxt = nextWeek();
    var cont = document.querySelector("[data-continue]");
    if (cont) {
      if (nxt) {
        cont.href = root + "weeks/week-" + pad(nxt) + ".html";
        cont.textContent = done === 0 ? "Start Week 1 →" : "Continue with Week " + nxt + " →";
      } else {
        cont.href = root + "weeks/week-16.html";
        cont.textContent = "All 16 weeks done. Nice work!";
      }
    }
    var start = state.startDate ? new Date(state.startDate + "T00:00:00") : null;
    document.querySelectorAll("[data-week-item]").forEach(function (li) {
      var n = +li.getAttribute("data-week-item");
      var a = li.querySelector("a");
      var st = li.querySelector(".status");
      a.classList.toggle("is-done", !!state.weeks[n]);
      a.classList.toggle("is-next", n === nxt);
      var label = state.weeks[n] ? "✓ Done" : (n === nxt ? "Up next" : "");
      if (start) {
        var d = new Date(start.getTime());
        d.setDate(d.getDate() + (n - 1) * 7);
        var when = "Week of " + d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
        label = label ? label + " · " + when : when;
      }
      st.textContent = label;
    });
  }

  var dateInput = document.querySelector("[data-start-date]");
  if (dateInput) {
    if (state.startDate) dateInput.value = state.startDate;
    dateInput.addEventListener("change", function () {
      if (dateInput.value) state.startDate = dateInput.value; else delete state.startDate;
      save(); paintHome();
    });
  }

  var resetBtn = document.querySelector("[data-reset]");
  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      if (window.confirm("Clear all your checkmarks, answers and start date on this device?")) {
        state = { tasks: {}, weeks: {}, answers: {}, path: state.path };
        save();
        window.location.reload();
      }
    });
  }

  // ---------- answer checker ----------
  function normText(s) { return String(s).toLowerCase().replace(/[^a-z0-9]/g, ""); }
  function parseNum(s) {
    var cleaned = String(s).replace(/[$,%\s]|days?|rows?|clients?|services?|codes?/gi, "");
    if (cleaned === "" || isNaN(+cleaned)) return null;
    return +cleaned;
  }
  function fmtAnswer(spec) {
    if (spec.type === "number") {
      var v = spec.answer;
      if (spec.unit === "$") return "$" + v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      if (spec.unit === "%") return v + "%";
      return v.toLocaleString() + (spec.unit ? " " + spec.unit : "");
    }
    return spec.answer;
  }
  function isCorrect(spec, val) {
    if (spec.type === "number") {
      var n = parseNum(val);
      return n !== null && Math.abs(n - spec.answer) <= spec.tolerance + 1e-9;
    }
    var v = normText(val);
    return v !== "" && spec.accept.some(function (a) { return normText(a) === v; });
  }

  function setupCheckpoints(key) {
    document.querySelectorAll(".checkpoint[data-key]").forEach(function (box) {
      var id = box.getAttribute("data-key");
      var spec = key[id];
      if (!spec) return;
      var tries = 0;
      var row = document.createElement("div");
      row.className = "row";
      var input = document.createElement("input");
      input.type = "text";
      input.autocomplete = "off";
      input.setAttribute("aria-label", "Your answer");
      input.placeholder = spec.type === "number" ? (spec.unit === "$" ? "e.g. 1234.56" : "type a number") : "type your answer";
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Check";
      row.appendChild(input);
      if (spec.unit && spec.unit !== "$") {
        var u = document.createElement("span");
        u.className = "unit";
        u.textContent = spec.unit;
        row.appendChild(u);
      }
      row.appendChild(btn);
      var fb = document.createElement("p");
      fb.className = "fb";
      fb.setAttribute("aria-live", "polite");
      box.appendChild(row);
      box.appendChild(fb);

      function markCorrect(val) {
        box.classList.remove("wrong");
        box.classList.add("correct");
        input.value = val;
        fb.textContent = "✓ Correct! " + fmtAnswer(spec);
        var reveal = box.querySelector(".reveal");
        if (reveal) reveal.remove();
      }
      if (state.answers[id]) markCorrect(state.answers[id]);

      function check() {
        var val = input.value.trim();
        if (!val) return;
        if (isCorrect(spec, val)) {
          state.answers[id] = val;
          save();
          markCorrect(val);
        } else {
          tries++;
          box.classList.remove("correct");
          box.classList.add("wrong");
          fb.textContent = tries === 1
            ? "Not quite. Check the 'Stuck?' box below and try again."
            : "Still not matching. Re-read the steps, or reveal the answer and work backwards.";
          if (tries >= 2 && !box.querySelector(".reveal")) {
            var r = document.createElement("button");
            r.type = "button";
            r.className = "link reveal";
            r.textContent = "Show me the answer";
            r.addEventListener("click", function () {
              fb.textContent = "The answer is " + fmtAnswer(spec) + (spec.note ? ". " + spec.note : ".");
              r.remove();
            });
            box.appendChild(r);
          }
        }
      }
      btn.addEventListener("click", check);
      input.addEventListener("keydown", function (e) { if (e.key === "Enter") check(); });
    });
  }

  if (document.querySelector(".checkpoint[data-key]")) {
    fetch(root + "data/answer-key.json")
      .then(function (r) { return r.json(); })
      .then(setupCheckpoints)
      .catch(function () {
        document.querySelectorAll(".checkpoint[data-key]").forEach(function (box) {
          var p = document.createElement("p");
          p.className = "note";
          p.textContent = "The answer checker couldn't load. It works on the live site (it can't run from a file opened on your computer).";
          box.appendChild(p);
        });
      });
  }

  paintMini();
  paintHome();
})();
