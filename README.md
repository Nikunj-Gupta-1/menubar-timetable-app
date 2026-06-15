# Next Class — Timetable Companion App

A set of lightweight companion applications designed to help students track their class schedule in real-time. The project includes two main variants:
1. **Next Class Desktop GUI App** (`next_class_app.py`): A modern desktop window application with a clean, themed UI.
2. **Next Class macOS Menubar App** (`next_class_menubar.py`): A quiet, non-obtrusive menu bar utility that lives in your Mac's top status bar.

Both apps automatically load schedule data, track the current class and its remaining time, display the next scheduled class, and show the first class of the next day. They also alert you when a class is about to start or end.

---

## 📂 Directory Structure

Here is the structure of the project repository:

```text
timetable-app/
├── Next Class.spec         # PyInstaller specification file for bundling the menubar app
├── build/                  # Build artifacts generated during compilation
├── dist/                   # Bundled standalone executable / .app packages
├── iconimg.icns            # macOS app icon (ICNS format)
├── iconimg.png             # Raw app icon (PNG format)
├── next_class_app.py       # GUI application using Tkinter and Sun Valley TTK theme
├── next_class_menubar.py   # macOS Menubar application using Rumps
├── setup.py                # py2app configuration to package the menubar app into a Mac App
├── timetable.json          # Schedule configuration data (JSON format)
└── venv/                   # Python virtual environment containing dependencies
```

---

## 🛠️ Prerequisites & Installation

### 1. Set up the Environment
It is recommended to run the apps inside a Python virtual environment. If not already activated:

```bash
# Create a virtual environment (optional)
python3 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies
Install the required packages using `pip`:

```bash
# For the Tkinter GUI modern theme:
pip install sv-ttk

# For the macOS Menubar application:
pip install rumps

# For packaging utilities (macOS only):
pip install setuptools py2app pyinstaller
```

---

## ⚙️ Configuration (`timetable.json`)

The schedule data is read from a JSON file. The applications will look for `timetable.json` in:
1. The directory containing the script.
2. Your user's `~/Documents` folder.

You can customize the timetable by editing [timetable.json](file:///Users/nikunjgupta/Downloads/PROJECTS/timetable-app/timetable.json).

### JSON Schema Structure

```json
{
  "timezone": "Asia/Kolkata",
  "weekStartsOn": "Monday",
  "periods": [
    { "id": 1, "start": "09:00", "end": "09:50" }
  ],
  "days": {
    "Monday": [
      {
        "period": 1,
        "course": "Design and analysis of Algorithms",
        "code": "CS F364",
        "section": "L1",
        "instructor": "Hussain Ahmed Chowdhary",
        "room": "222",
        "nickname": "DAA"
      }
    ]
  }
}
```

### Key Parameters:
* **`periods`**: Defines the school/university time slots with integer IDs.
* **`days`**: Map of weekdays (Monday through Sunday) containing lists of classes.
  * **`period`**: The period ID from the list defined above.
  * **`course`**: Full name of the course.
  * **`code`** / **`section`**: Course code and class section designation.
  * **`room`**: Location of the class.
  * **`nickname`**: A short name (up to 5-6 characters) displayed on the menubar interface (e.g., "DAA" for Design and analysis of Algorithms).

---

## 🚀 How to Run the Applications

### 1. Desktop GUI Application
Runs a standalone GUI window with a modern, system-themed light interface showing the full schedule state.

```bash
python next_class_app.py
```

* **Interactive JSON Selector**: If no `timetable.json` is found initially, the app opens a file dialogue prompting you to select one.
* **Status Updates**: Refreshes automatically every 60 seconds, or manually by clicking the **Refresh** button.
* **Alert Notifications**: Plays a system bell and displays a pop-up alert when a class has `15 minutes` left to end or is starting in `15 minutes`.

---

### 2. macOS Menubar Application
Runs a status bar utility in the macOS menubar.

```bash
python next_class_menubar.py
```

* **Status Indicators**:
  * `▶ DAA` : Class is currently in progress (shows nickname).
  * `⏳ DL` : A class is upcoming next (shows nickname).
  * `📚` : No classes currently active or upcoming today.
  * `❌` : Error reading or loading `timetable.json`.
* **Menubar Menu Options**:
  * **Now / Next**: Displays a macOS alert popup with details about the current class, next class, room number, and exact countdown timer.
  * **Refresh**: Instantly reloads the schedule data and updates the status.
  * **Choose JSON...**: Tips on how to change files.
  * **Quit**: Exits the menubar application.
* **Desktop Notifications**: Uses macOS's User Notification Center to alert you when a class starts/ends soon.

---

## 📦 Packaging and Bundling (Building Executables)

You can compile these scripts into native executables so they run without terminal commands.

### Method A: Build macOS App Bundle using `py2app`
Using the configured [setup.py](file:///Users/nikunjgupta/Downloads/PROJECTS/timetable-app/setup.py) file:

```bash
# Build the macOS .app package
python setup.py py2app
```
This builds `Next Class.app` inside the `dist/` folder. It sets `LSUIElement` to `True` which keeps the application purely in the menu bar and hides it from the dock.

---

### Method B: Build using PyInstaller
Using the configured [Next Class.spec](file:///Users/nikunjgupta/Downloads/PROJECTS/timetable-app/Next%20Class.spec) file:

```bash
pyinstaller "Next Class.spec"
```
This will compile and package the app using PyInstaller, bundle the `timetable.json` and custom icon files, and place the output in the `dist/` directory.
