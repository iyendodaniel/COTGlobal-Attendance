# Church Attendance System

A web-based system built with **Django** to manage member profiles, track church attendance, and automate attendance reporting.

---

## Features

* Admin dashboard for managing members.
* Complete member profiles for children, teens, and workers.
* Role-based fields:

  * **Children**: Parent info, age, gender.
  * **Teens**: Phone number, gender.
  * **Workers**: Phone number, gender, department.
* Attendance marking and tracking.
* Form validation (phone number, gender, age, etc.).
* Messages for errors and success notifications.

---

## Tech Stack

* **Backend**: Python, Django
* **Frontend**: HTML, CSS, JavaScript
* **Database**: SQLite (can switch to PostgreSQL)
* **Version Control**: Git & GitHub

---

## Installation

1. **Clone the repo**

```bash
git clone https://github.com/iyendodaniel/repo.git
cd repo
```

2. **Create virtual environment**

```bash
python -m venv venv
```

3. **Activate environment**

* Windows: `venv\Scripts\activate`
* Mac/Linux: `source venv/bin/activate`

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Apply migrations**

```bash
python manage.py migrate
```

6. **Run server**

```bash
python manage.py runserver
```

---

## Usage

1. Log in as an admin.
2. Navigate to **Complete Profile**.
3. Select a member and fill missing details.
4. Save the profile.
5. Admin can view and manage attendance reports.

---

## .gitignore

* `.env` – environment variables
* `db/` – database folder
* `venv/` – virtual environment

---

## Future Improvements

* Add **attendance reporting dashboard**.
* Integrate **SMS notifications** for attendance reminders.
* Add **export to Excel / CSV** feature.

---

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/xyz`).
3. Commit changes (`git commit -m "Add xyz feature"`).
4. Push to branch (`git push origin feature/xyz`).
5. Open a Pull Request.

---

## License

MIT License © 2025 Iyendo Daniel Okeoghene
