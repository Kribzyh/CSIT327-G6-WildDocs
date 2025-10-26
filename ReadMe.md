# WildDocs 📚

A comprehensive student document management system built with Django and Supabase, designed to streamline document handling and profile management for academic institutions.

## 🛠️ Tech Stack

- **Backend Framework:** Django 5.2.6
- **Programming Language:** Python 3.13
- **Database:** PostgreSQL (Supabase)
- **Cloud Platform:** Supabase (Database, Authentication, Storage)
- **Frontend:** HTML5, CSS3, JavaScript
- **Package Management:** Pipenv
- **Authentication:** Django + Supabase Auth
- **File Storage:** Supabase Storage

## 🚀 Setup & Run Instructions

> IMPORTANT: Do NOT commit your `.env` file. Copy `.env.example` to `.env` and fill in secrets locally. The repository should never contain live keys.

### Prerequisites

- Python 3.13 or higher
- Pipenv (for virtual environment and dependency management)
- Supabase account and project

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
   pipenv install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env file with your Supabase credentials
   # See DEVELOPER_SETUP.md for detailed instructions
   ```

5. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:8000/`

### 🛑 Stopping the Server

To stop the Django development server, press `Ctrl + C` in the terminal.

### 🔧 Environment Variables Required

Create a `.env` file in the project root with the following variables:

```properties
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# Database Configuration
DATABASE_URL=your_supabase_postgres_connection_string

# Django Configuration
SECRET_KEY=your_django_secret_key
DEBUG=True
```

> **For Developers:** See `DEVELOPER_SETUP.md` for detailed setup instructions and credential sharing information.

## 👥 Team Members

| Name | Role | CIT-U Email |
|------|------|-------------|
| Cordero, Camila Rose A. | Frontend | camilarose.cordero@cit.edu |
| Delposo, Kerby | Lead Developer | kerby.delposo@cit.edu |
| Cayacap, Denn Anton Marc | Backend | dennantonmarc.cayacap@cit.edu |

## 🌐 Deployed Link

🚧 **Deployment Status:** Not yet deployed

## 📱 Features

- **User Authentication:** Secure student login and registration system with Supabase Auth
- **Dashboard:** Personalized student dashboard with profile management
- **Profile Management:** Edit and update student profile information with image uploads
- **Document Management:** Comprehensive document handling and request system
- **File Storage:** Secure file storage using Supabase Storage
- **Real-time Database:** PostgreSQL database with Supabase integration
- **Responsive Design:** Mobile-friendly interface
- **Request System:** Document request tracking and management

## 📁 Project Structure

```
WildDocs/
├── accounts/           # User authentication and account management
│   ├── models.py      # Student account models with Supabase integration
│   ├── views.py       # Authentication views
│   ├── forms.py       # User registration and login forms
│   └── templates/     # Login and registration templates
├── dashboard/          # Student dashboard functionality
│   ├── views.py       # Dashboard and profile management views
│   └── templates/     # Dashboard and profile edit templates
├── index/             # Home page and main navigation
│   ├── views.py       # Landing page views
│   └── templates/     # Base templates and home page
├── request/           # Document request management
│   ├── models.py      # Request tracking models
│   ├── views.py       # Request handling views
│   └── templates/     # Request management templates
├── services/          # External service integrations
│   └── supabase_client.py  # Supabase service wrapper
├── media/             # Local media files
├── profile_pictures/  # Local profile picture storage
├── WildDocs/          # Main Django project settings
│   ├── settings.py    # Django configuration with Supabase
│   └── urls.py        # URL routing
├── .env.example       # Environment variables template
├── DEVELOPER_SETUP.md # Developer setup instructions
├── manage.py          # Django management script
├── Pipfile            # Python dependencies
└── README.md          # Project documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### For New Developers

1. Read the `DEVELOPER_SETUP.md` for detailed setup instructions
2. Request access to the Supabase project from the team
3. Set up your local environment with the provided credentials
4. Follow the coding standards established in the project

## 🔧 Technologies & Dependencies

### Core Dependencies
- **Django 5.2.6:** Web framework
- **supabase:** Python client for Supabase
- **psycopg2:** PostgreSQL adapter
- **Pillow:** Image processing for profile pictures
- **python-dotenv:** Environment variable management

### Development Tools
- **Pipenv:** Dependency management
- **Git:** Version control
- **VS Code:** Recommended IDE

## 🌐 Supabase Integration

This project leverages Supabase for:
- **Database:** PostgreSQL database with real-time capabilities
- **Authentication:** User registration and login
- **Storage:** File uploads and profile picture storage
- **API:** RESTful API access to data

## 📞 Support

If you need help with setup or encounter issues:
1. Check the `DEVELOPER_SETUP.md` file
2. Review the project documentation
3. Contact the development team

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Last updated: October 2025*

