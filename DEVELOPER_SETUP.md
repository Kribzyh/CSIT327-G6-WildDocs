# WildDocs - Developer Setup Guide

IMPORTANT: Do NOT commit your `.env` file. Use `.env.example` as a template and keep real secrets local only.

## Setting up the Supabase Integration

This project uses Supabase for:
- PostgreSQL Database
- User Authentication
- File Storage (profile pictures)

### Prerequisites
- Python 3.x
- pip or pipenv
- Git

### Setup Instructions

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd WildDocs
   ```

2. **Install dependencies**:
   ```bash
   # Using pipenv (recommended)
   pipenv install
   pipenv shell

   # OR using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Ask the project owner for the actual Supabase credentials
   - Fill in the values in your `.env` file

4. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

### Environment Variables Needed

You'll need these Supabase credentials from the project owner:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anonymous key (for client operations)
- `SUPABASE_SERVICE_KEY`: Supabase service role key (for admin operations)
- `DATABASE_URL`: PostgreSQL connection string

### Supabase Project Access

**Option 1: Team Member Access (Recommended)**
- Ask the project owner to invite you as a team member to their Supabase project
- This gives you access to the dashboard, database, and other features

**Option 2: Shared Credentials**
- Use the shared credentials provided by the project owner
- This gives you read/write access but no dashboard access

### Getting Your Own Supabase Project (For Testing)

If you want to set up your own Supabase instance for testing:

1. Go to [https://supabase.com](https://supabase.com)
2. Create a new project
3. Get your project URL and keys from Settings → API
4. Update your `.env` file with your own credentials
5. Run the migrations to set up the database schema

### Project Structure

- **accounts/**: User authentication and profile management
- **dashboard/**: User dashboard with profile editing
- **index/**: Landing page
- **request/**: Document request functionality
- **services/**: Supabase integration service
- **WildDocs/**: Django project settings

### Supabase Integration

The project uses a custom Supabase service (`services/supabase_client.py`) that handles:
- User authentication
- File uploads to Supabase Storage
- Database operations through Django ORM (connected to Supabase PostgreSQL)

### Need Help?

If you encounter issues:
1. Make sure your `.env` file has all required variables
2. Verify your Supabase credentials are correct
3. Check that your Supabase project is active
4. Ensure you have the right permissions in the Supabase project