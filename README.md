# Coursework Planner

A desktop app for tracking courses, assessments, and deadlines - built with Python and PyQt5.

Each course is shown as a collapsible card with a color you choose, a completion ring showing how much of its coursework is done, and your current weighted grade. Assessments are listed soonest-due first, with a quick way to mark them complete and hide them once they are. A calendar panel on the side shows the month at a glance (with a colored dot per course on each due date) or a week view broken out by day.

## Features

- **Courses** - add, rename, recolor, or delete a course. Each one tracks its own list of assessments.
- **Assessments** - name, type (assignment, quiz, test, exam, lab, project, or your own), due date, weight, and grade once graded.
- **Completion tracking** - a ring on each course card fills in as assessments are marked done, with the percentage shown inside it.
- **Grade calculation** - a weighted average grade is calculated automatically from graded assessments.
- **Calendar** - month view with colored due-date dots per course, and a week view listing what's due each day.
- **Local storage** - everything is saved to a `data.JSON` file next to the app, no account or internet connection required.

## Requirements

- Python 3.10 or newer
- [PyQt5](https://pypi.org/project/PyQt5/)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
   ```

2. **(Recommended) Create a virtual environment**
   ```bash
   python -m venv venv
   ```
   Activate it:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**
   ```bash
   python main.py
   ```

On first launch, the app creates an empty `data.JSON` file to store your courses. Use **+ Add course** to get started.

## Project structure

```
├── main.py            # Entry point
├── main_window.py      # Main window: assembles the courses panel and calendar
├── controller.py        # Mediates between the GUI and the model/storage layers
├── course.py            # Course model
├── assessment.py         # Assessment model
├── storage.py            # Reads/writes data.JSON
├── dialogs.py             # Add/edit dialogs for courses and assessments
├── course_card.py          # Collapsible course card widget
├── ring_widget.py           # Completion ring widget
├── calendar_view.py          # Month/week calendar panel
└── data.JSON                  # Your saved courses and assessments (created on first run)
```

## Running tests

The model and controller layers have automated tests (`test_weight_tracking.py`) that don't require PyQt5 or a display, so they run anywhere:

```bash
pytest -v
```

## Known limitations

- Assessments are tracked by due **date** only, not a specific time - the week view shows what's due on a given day rather than an hour-by-hour schedule.
- Data is stored locally in a single JSON file; there is no sync or backup built in.
