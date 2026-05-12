import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'college_erp.settings')
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()
client = Client(SERVER_NAME='localhost')
user = User.objects.filter(is_superuser=True).first()
if user:
    client.force_login(user)
    try:
        response = client.get('/dashboard/admin/partial/students/')
        print('STATUS:', response.status_code)
        if response.status_code == 500:
            import re
            html = response.content.decode()
            m = re.search(r'(?i)<textarea.*?id="traceback_area".*?>(.*?)</textarea>', html, re.DOTALL)
            if m:
                print('TRACEBACK FOUND:')
                print(m.group(1))
            else:
                print('DUMPING TOP 2000 CHARS:')
                print(html[:2000])
    except Exception as e:
        print('EXCEPTION DURING GET:', e)
        import traceback
        traceback.print_exc()
else:
    print('No user')
