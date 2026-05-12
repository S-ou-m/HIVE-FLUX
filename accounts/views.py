from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from core.models import College
from accounts.models import Student, Faculty, UserRole

def login_view(request):
    colleges = College.objects.all()
    
    if request.method == 'POST':
        role = request.POST.get('role')
        college_id = request.POST.get('college')
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            return render(request, 'auth/login.html', {'colleges': colleges, 'error': 'Please provide both identifier and key.'})

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 1. Validate College
            if user.college and str(user.college.id) != college_id:
                return render(request, 'auth/login.html', {'colleges': colleges, 'error': 'Invalid credentials for the selected institution.'})
            
            # 2. Validate Role matches actual database profile
            is_valid_role = False
            if role == 'student':
                is_valid_role = Student.objects.filter(user=user).exists()
            elif role == 'faculty':
                is_valid_role = Faculty.objects.filter(user=user).exists()
            elif role == 'admin':
                is_valid_role = user.is_staff or user.is_superuser or UserRole.objects.filter(user=user, role__name__icontains='admin').exists()
            
            if not is_valid_role:
                return render(request, 'auth/login.html', {'colleges': colleges, 'error': f'Invalid credentials. You are not registered as a {role.capitalize()}.'})
            
            # All checks passed, log them in
            login(request, user)
            request.session['college_id'] = college_id
            
            # Redirect based on role
            if role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'student':
                return redirect('student_dashboard')
            elif role == 'faculty':
                return redirect('faculty_dashboard')
            else:
                return redirect('admin_dashboard')
                
        else:
            return render(request, 'auth/login.html', {'colleges': colleges, 'error': 'Invalid username or password.'})

    return render(request, 'auth/login.html', {'colleges': colleges})

def logout_view(request):
    logout(request)
    return redirect('login')
