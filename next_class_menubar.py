import json
from datetime import datetime
from pathlib import Path

import rumps

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


def get_nickname(cls_dict) -> str:
    """Return short label for the course (<= 5–6 chars)."""
    nick = cls_dict.get("nickname")
    if nick:
        return nick
    # Fallback: first word of course name, truncated
    course = cls_dict.get("course", "").strip()
    if not course:
        return "CL"
    base = course.split()[0][:6]
    return base


class NextClassMenuBarApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="Next Class",
            title="📚",          # default icon; will be updated with nickname
            quit_button=None,
        )
        self.json_path = self.find_default_json()
        self.timetable = None
        self.last_notification_key = None

        self.menu = [
            rumps.MenuItem("Now / Next"),
            rumps.MenuItem("Refresh"),
            rumps.MenuItem("Choose JSON…"),
            None,
            rumps.MenuItem("Quit"),
        ]

        self.load_timetable()
        self.update_status()

        self.timer = rumps.Timer(self.tick, 60)
        self.timer.start()

    # ---------- file handling ----------

    def find_default_json(self) -> Path | None:
        here = Path(__file__).resolve().parent
        bundled = here / DEFAULT_JSON_NAME
        docs = Path.home() / "Documents" / DEFAULT_JSON_NAME
        if bundled.exists():
            return bundled
        if docs.exists():
            return docs
        return None

    def load_timetable(self):
        if not self.json_path:
            return
        try:
            self.timetable = load_json(self.json_path)
        except Exception as e:
            rumps.alert("Next Class", f"Could not load timetable JSON.\n\n{e}")
            self.timetable = None

    # ---------- actions ----------

    @rumps.clicked("Refresh")
    def refresh_clicked(self, _):
        self.update_status()

    @rumps.clicked("Choose JSON…")
    def choose_json_clicked(self, _):
        rumps.alert(
            "Choose JSON",
            "Please place your timetable.json in Documents or next to the app\n"
            "and restart, or edit json_path in the code.",
        )

    @rumps.clicked("Now / Next")
    def show_now_next(self, _):
        text = self.build_popup_text()
        rumps.alert("Next Class", text)

    @rumps.clicked("Quit")
    def quit_clicked(self, _):
        rumps.quit_application()

    def tick(self, _):
        self.update_status()

    # ---------- core status logic ----------

    def update_status(self):
        if not self.timetable and self.json_path:
            self.load_timetable()
        if not self.timetable:
            self.title = "❌"
            return

        now = datetime.now()
        current_cls = find_current_class(self.timetable, now)
        next_cls = find_upcoming_class(self.timetable, now)

        # Menu-bar title: icon + short nickname
        if current_cls:
            nick = get_nickname(current_cls["class"])
            self.title = f"▶ {nick}"
        elif next_cls:
            nick = get_nickname(next_cls["class"])
            self.title = f"⏳ {nick}"
        else:
            self.title = "📚"

        self.notify_if_needed(current_cls, next_cls)

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
            rumps.notification(title, "", message)

    def build_popup_text(self) -> str:
        if not self.timetable:
            return "No timetable loaded."

        now = datetime.now()
        lines = [now.strftime("Now · %A, %d %b %Y · %I:%M %p"), ""]

        current_cls = find_current_class(self.timetable, now)
        next_cls = find_upcoming_class(self.timetable, now)

        if current_cls:
            c = current_cls["class"]
            p = current_cls["period"]
            lines += [
                "Current class:",
                f"{c['course']} ({c['code']} {c['section']})",
                f"{current_cls['day']} · ends at {p['end']}",
                f"Room: {c['room']}",
                f"Ends in {humanize_minutes(current_cls['minutes_left'])}",
                "",
            ]
        else:
            lines += ["Current class: None", ""]

        if next_cls:
            c = next_cls["class"]
            p = next_cls["period"]
            lines += [
                "Next class:",
                f"{c['course']} ({c['code']} {c['section']})",
                f"{next_cls['day']} · {p['start']}–{p['end']}",
                f"Room: {c['room']}",
                f"Starts in {humanize_minutes(next_cls['minutes_left'])}",
                "",
            ]
        else:
            lines += ["Next class: None in next 7 days", ""]

        return "\n".join(lines)


if __name__ == "__main__":
    NextClassMenuBarApp().run()