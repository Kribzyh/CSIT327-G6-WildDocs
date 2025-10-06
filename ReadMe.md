# WildDocs 📚

A comprehensive student document management system built with Django, designed to streamline document handling and profile management for academic institutions.

## 🛠️ Tech Stack

- **Backend Framework:** Django 5.2.6
- **Programming Language:** Python 3.13
- **Database:** SQLite3 (Development)
- **Frontend:** HTML5, CSS3, JavaScript
- **Package Management:** Pipenv
- **Authentication:** Django's built-in authentication system

## 🚀 Setup & Run Instructions

### Prerequisites

- Python 3.13 or higher
- Pipenv (for virtual environment and dependency management)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Kribzyh/WildDocs.git
   cd WildDocs
   ```

2. **Install Pipenv (if not already installed)**
   ```bash
   pip install pipenv
   ```

3. **Install dependencies and activate virtual environment**
   ```bash
   pipenv install
   pipenv shell
   ```

4. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000/`

### � Stopping the Server

To stop the Django development server, press `Ctrl + C` in the terminal.

## 👥 Team Members

| Name | Role | CIT-U Email |
|------|------|-------------|
| Cordero, Camila Rose A. | Frontend | camilarose.cordero@cit.edu |
| Delposo, Kerby | Backend | kerby.delposo@cit.edu |
| Cayacap, Denn Anton Marc | Backend | dennantonmarc.cayacap@cit.edu |

## 🌐 Deployed Link

🚧 **Deployment Status:** Not yet deployed

*The deployed link will be updated once the application is hosted on a production server.*

## 📱 Features

- **User Authentication:** Secure student login and registration system
- **Dashboard:** Personalized student dashboard with profile management
- **Profile Management:** Edit and update student profile information
- **Document Management:** Comprehensive document handling system
- **Responsive Design:** Mobile-friendly interface

## 📁 Project Structure

```
WildDocs/
├── accounts/          # User authentication and account management
├── dashboard/         # Student dashboard functionality
├── index/            # Home page and main navigation
├── profile_pictures/ # User profile image storage
├── WildDocs/         # Main Django project settings
├── manage.py         # Django management script
├── db.sqlite3        # SQLite database
├── Pipfile           # Python dependencies
└── README.md         # Project documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## � License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Last updated: October 2025*

