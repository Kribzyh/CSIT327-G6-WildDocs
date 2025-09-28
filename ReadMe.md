📄 `WildDocs_Project_Documentation.md`

# WildDocs - Project Documentation

## 🛠️ Project Setup

### 1. Environment Setup

#### ✅ Install Python

Make sure the latest version of Python is installed.

Verify installation:

```bash
python --version
````

---

#### ✅ Create Project Directory

```bash
mkdir WildDocs
cd WildDocs
```

#### ✅ Install Pipenv (if not installed yet)

```bash
pip install pipenv
```

#### ✅ Create and Activate Virtual Environment with Pipenv
```bash
pipenv install django
pipenv shell
```

#### ✅ Start Django Project
```bash
django-admin startproject WildDocs .
```

> **Note:** The `.` at the end prevents Django from creating an extra subdirectory.

---

##### 🔍 What it does:

* `django-admin startproject WildDocs` creates a new Django project named **WildDocs**.
* Normally, this creates a subdirectory with the same name as the project.

**Without the period (`.`), your folder structure would look like:**

```
WildDocs/
└── WildDocs/
    └── WildDocs/   # parent folder / project folder / inner Django module
```

---

### 2. ✅ Test Django

Start the development server:

```bash
python manage.py runserver
```

After running the command, you should see something like:

```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).

You have 18 unapplied migration(s). Your project may not work properly until you apply the migrations for app(s): admin, auth, contenttypes, sessions.
Run 'python manage.py migrate' to apply them.

September 22, 2025 - 22:10:24
Django version 5.2.6, using settings 'WildDocs.settings'
Starting development server at http://127.0.0.1:8000/   <<<<<<-----------!!!!!!!!!   (EYES HERE!!!) --> ctrl + click this link
Quit the server with CTRL-BREAK.

WARNING: This is a development server. Do not use it in a production setting. Use a production WSGI or ASGI server instead.
```

---

### 🛑 Stopping the Server

To stop the Django development server:

```bash
ctrl + c
```

