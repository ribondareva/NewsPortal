# News Portal

A Django-based news portal where users can stay updated with the latest articles and news. The platform supports two main types of users: **regular users** and **authors**. Authors can create, edit, or delete posts (articles or news). Registered users can subscribe to specific categories to receive weekly email digests.

---

## Features

### General Features
- **Responsive Design**: Accessible on both desktop and mobile devices.
- **Category-Based Content**: News and articles are organized into categories.
- **User Authentication**: Secure registration, login, and profile management.

### Author Features
- Create, edit, or delete posts.
- Manage categories for their articles.
- Dashboard to monitor their posts' performance.

### Regular User Features
- Subscribe to categories of interest.
- Weekly email digest with articles from subscribed categories.
- Comment on articles (optional feature).

### Email Notifications
- Automated weekly email digests.
- Fully customizable email templates.
- Integration with SMTP or third-party email services (e.g., SendGrid, Postmark).

---

## Tech Stack

### Backend
- Python (Django Framework)
- SQLite3 (Default Database)

### Frontend
- HTML, CSS, JavaScript (with optional frameworks like Bootstrap)

### Additional Tools
- Celery for scheduling weekly digests.
## Installation

### 1. Clone the Repository
- git clone https://github.com/ribondareva/NewsPortal.git
- cd NewsPortal

### 2. Set Up Virtual Environment
- python -m venv venv
- source venv/bin/activate 

### 3. Set Up the Database
python manage.py migrate

 ### 4. Collect Static Files
 python manage.py collectstatic

 ### 5. Run the Development Server
 python manage.py runserver


## Usage

 ### For Authors
Register and request author permissions from an admin.
Log in to access the author dashboard.
Create, edit, or delete posts.

 ### For Regular Users
Register and log in.
Browse posts by category or search by keyword.
Subscribe to categories to receive weekly email digests.
