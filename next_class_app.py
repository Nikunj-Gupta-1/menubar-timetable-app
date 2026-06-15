import json
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import sv_ttk  # modern theme

DEFAULT_JSON_NAME = "timetable.json"
NOTIFICATION_LEAD_MINUTES = 15
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def hhmm_to_minutes(text: str) -> int:
    h, m = map(int, text.split(":"))
    return h * 60 + m


def humanize_minutes(total: int) -> str:
    days, rem = divmod(total, 1440)
    hours, mins = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days} day" + ("s" if days != 1 else ""))
    if hours:
        parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
    if mins or not parts:
        parts.append(f"{mins} minute" + ("s" if mins != 1 else ""))
    return ", ".join(parts)


def build_period_map(timetable):
    return {p["id"]: p for p in timetable["periods"]}


def find_current_class(timetable, now=None):
    now = now or datetime.now()
    day = now.strftime("%A")
    current_minutes = now.hour * 60 + now.minute
    periods = build_period_map(timetable)
    for cls in timetable.get("days", {}).get(day, []):
        period = periods[cls["period"]]
        start = hhmm_to_minutes(period["start"])
        end = hhmm_to_minutes(period["end"])
        if start <= current_minutes < end:
            return {
                "day": day,
                "class": cls,
                "period": period,
                "minutes_left": end - current_minutes,
            }
    return None


def find_upcoming_class(timetable, now=None):
    now = now or datetime.now()
    current_day = now.strftime("%A")
    current_idx = DAYS.index(current_day)
    current_minutes = now.hour * 60 + now.minute
    periods = build_period_map(timetable)

    for offset in range(7):
        day = DAYS[(current_idx + offset) % 7]
        classes = timetable.get("days", {}).get(day, [])
        for cls in classes:
            period = periods[cls["period"]]
            start = hhmm_to_minutes(period["start"])
            if offset > 0 or start > current_minutes:
                mins_left = start - current_minutes + offset * 1440
                return {
                    "day": day,
                    "class": cls,
                    "period": period,
                    "minutes_left": mins_left,
                }
    return None


def find_next_day_first_class(timetable, now=None):
    now = now or datetime.now()
    current_day = now.strftime("%A")
    current_idx = DAYS.index(current_day)
    periods = build_period_map(timetable)

    for offset in range(1, 8):
        day = DAYS[(current_idx + offset) % 7]
        classes = timetable.get("days", {}).get(day, [])
        if classes:
            cls = classes[0]
            return {"day": day, "class": cls, "period": periods[cls["period"]]}
    return None


class NextClassApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Next Class")
        self.root.geometry("520x420")
        self.root.minsize(480, 360)

        # Use system-like appearance
        self.root.configure(padx=16, pady=16)

        self.json_path: Path | None = self.find_default_json()
        self.last_notification_key = None

        # Layout: top info frame, card frame, bottom buttons
        self.build_header()
        self.build_content()
        self.build_buttons()

        self.refresh()
        self.root.after(60_000, self.auto_refresh)

    # ---------- UI building ----------

    def build_header(self):
        top = ttk.Frame(self.root)
        top.pack(fill="x", pady=(0, 12))

        title = ttk.Label(
            top, text="Next Class", font=("SF Pro Text", 20, "bold")
        )
        title.pack(anchor="center")

        self.path_label = ttk.Label(
            top,
            text=self.path_text(),
            wraplength=480,
            justify="center",
            foreground="#888888",
        )
        self.path_label.pack(anchor="center", pady=(4, 0))

    def build_content(self):
        card = ttk.Frame(self.root, padding=12)
        card.pack(fill="both", expand=True)

        # Use a Treeview-like layout with labels instead of raw Text
        self.now_label = ttk.Label(card, font=("SF Mono", 11))
        self.now_label.pack(anchor="w", pady=(0, 8))

        self.current_title = ttk.Label(card, font=("SF Pro Text", 13, "bold"))
        self.current_title.pack(anchor="w")

        self.current_details = ttk.Label(
            card, justify="left", wraplength=480, font=("SF Pro Text", 11)
        )
        self.current_details.pack(anchor="w", pady=(0, 10))

        self.next_title = ttk.Label(card, font=("SF Pro Text", 13, "bold"))
        self.next_title.pack(anchor="w")

        self.next_details = ttk.Label(
            card, justify="left", wraplength=480, font=("SF Pro Text", 11)
        )
        self.next_details.pack(anchor="w", pady=(0, 10))

        self.tomorrow_title = ttk.Label(card, font=("SF Pro Text", 13, "bold"))
        self.tomorrow_title.pack(anchor="w")

        self.tomorrow_details = ttk.Label(
            card, justify="left", wraplength=480, font=("SF Pro Text", 11)
        )
        self.tomorrow_details.pack(anchor="w")

    def build_buttons(self):
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", pady=(12, 0))

        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)
        bottom.columnconfigure(2, weight=1)

        ttk.Button(bottom, text="Refresh", command=self.refresh).grid(
            row=0, column=0, padx=4
        )
        ttk.Button(bottom, text="Choose JSON", command=self.choose_json).grid(
            row=0, column=1, padx=4
        )
        ttk.Button(bottom, text="Quit", command=self.root.destroy).grid(
            row=0, column=2, padx=4
        )

    # ---------- JSON + status ----------

    def find_default_json(self) -> Path | None:
        here = Path(__file__).resolve().parent
        bundled = here / DEFAULT_JSON_NAME
        docs = Path.home() / "Documents" / DEFAULT_JSON_NAME
        if bundled.exists():
            return bundled
        if docs.exists():
            return docs
        return None

    def path_text(self) -> str:
        return f"JSON: {self.json_path}" if self.json_path else "JSON: not selected"

    def choose_json(self):
        selected = filedialog.askopenfilename(
            title="Choose timetable JSON", filetypes=[("JSON files", "*.json")]
        )
        if selected:
            self.json_path = Path(selected)
            self.path_label.config(text=self.path_text())
            self.refresh()

    def notify_if_needed(self, current_cls, next_cls):
        title = "Next Class"
        message = None
        key = None

        if current_cls and current_cls["minutes_left"] <= NOTIFICATION_LEAD_MINUTES:
            c = current_cls["class"]
            message = f'{c["course"]} ends in {humanize_minutes(current_cls["minutes_left"])}'
            key = ("current", c["course"], current_cls["day"], current_cls["period"]["end"])
        elif next_cls and next_cls["minutes_left"] <= NOTIFICATION_LEAD_MINUTES:
            c = next_cls["class"]
            message = (
                f'{c["course"]} starts in {humanize_minutes(next_cls["minutes_left"])}'
                f' • Room {c["room"]}'
            )
            key = ("next", c["course"], next_cls["day"], next_cls["period"]["start"])

        if message and key != self.last_notification_key:
            self.last_notification_key = key
            try:
                self.root.bell()
                messagebox.showinfo(title, message)
            except Exception:
                pass

    def refresh(self):
        if not self.json_path:
            self.choose_json()
            if not self.json_path:
                return

        try:
            timetable = load_json(self.json_path)
        except Exception as e:
            messagebox.showerror("Next Class", f"Could not load timetable JSON.\n\n{e}")
            return

        now = datetime.now()
        self.path_label.config(text=self.path_text())
        self.now_label.config(
            text=now.strftime("Now · %A, %d %b %Y · %I:%M %p")
        )

        current_cls = find_current_class(timetable, now)
        next_cls = find_upcoming_class(timetable, now)
        next_day_cls = find_next_day_first_class(timetable, now)

        # Current class
        if current_cls:
            c = current_cls["class"]
            p = current_cls["period"]
            self.current_title.config(text="Current class")
            self.current_details.config(
                text=(
                    f"{c['course']}  ({c['code']} {c['section']})\n"
                    f"{current_cls['day']} · ends at {p['end']}\n"
                    f"Room: {c['room']}\n"
                    f"Ends in {humanize_minutes(current_cls['minutes_left'])}"
                )
            )
        else:
            self.current_title.config(text="Current class")
            self.current_details.config(text="None")

        # Next class
        if next_cls:
            c = next_cls["class"]
            p = next_cls["period"]
            self.next_title.config(text="Next class")
            self.next_details.config(
                text=(
                    f"{c['course']}  ({c['code']} {c['section']})\n"
                    f"{next_cls['day']} · {p['start']}–{p['end']}\n"
                    f"Room: {c['room']}\n"
                    f"Starts in {humanize_minutes(next_cls['minutes_left'])}"
                )
            )
        else:
            self.next_title.config(text="Next class")
            self.next_details.config(text="None in the next 7 days")

        # Next day with class
        if next_day_cls:
            c = next_day_cls["class"]
            p = next_day_cls["period"]
            self.tomorrow_title.config(text="Next day with class")
            self.tomorrow_details.config(
                text=(
                    f"{next_day_cls['day']}\n"
                    f"First class: {c['course']} ({c['code']} {c['section']})\n"
                    f"Starts at {p['start']} · Room: {c['room']}"
                )
            )
        else:
            self.tomorrow_title.config(text="Next day with class")
            self.tomorrow_details.config(text="None")

        # Notify if needed
        self.notify_if_needed(current_cls, next_cls)

    def auto_refresh(self):
        self.refresh()
        self.root.after(60_000, self.auto_refresh)


def main():
    root = tk.Tk()
    # Apply modern theme: choose light or dark
    sv_ttk.use_light_theme()  # or sv_ttk.use_light_theme()
    app = NextClassApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()