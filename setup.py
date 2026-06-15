from setuptools import setup

APP = ['next_class_menubar.py']
DATA_FILES = ['timetable.json']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['rumps'],
    'plist': {
        'CFBundleName': 'Next Class',
        'CFBundleDisplayName': 'Next Class',
        'CFBundleIdentifier': 'com.nikunj.nextclass.menubar',
        'LSUIElement': True,  # menu-bar-only, hides Dock icon
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)