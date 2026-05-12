import requests

# We need to login first to get the session cookie
session = requests.Session()

# Get login page to get CSRF token
r1 = session.get('http://127.0.0.1:8000/login/')
csrf_token = r1.cookies.get('csrftoken')

# We don't know the exact username/password, but maybe we can just look at the stack trace 
# without logging in if there's a 500 on login? No, it's on /dashboard/admin/partial/students/
# Let's just create a superuser and login via code in django, but how to pass the session cookie to `requests`?
# Better: just look at the Django project's internal state. But the internal state is fine.
