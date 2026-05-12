from core.models import College
from django.shortcuts import redirect
from django.urls import reverse

class TenantMiddleware:
    """
    Middleware to attach the active College (Tenant) to the request object.
    This enables easy multi-tenancy filtering across all views.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # If the user belongs to a specific college, that is their tenant
            request.college = request.user.college
            
            # If user is a superuser (no specific college attached), 
            # they can assume the college they selected during login
            if not request.college and 'college_id' in request.session:
                request.college = College.objects.filter(id=request.session['college_id']).first()
        else:
            request.college = None

        response = self.get_response(request)
        return response

class HtmxRedirectMiddleware:
    """
    Middleware to handle HTMX redirects gracefully.
    If an HTMX request is redirected to the login page (e.g. session expired),
    we send a 'HX-Redirect' header so the browser redirects the whole page 
    instead of trying to load the login page into a partial div.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # If it's an HTMX request and it's a redirect (301, 302)
        if request.headers.get('HX-Request') and 300 <= response.status_code < 400:
            # Move the redirect URL to the HX-Redirect header
            redirect_url = response.url if hasattr(response, 'url') else response.get('Location')
            if redirect_url:
                response['HX-Redirect'] = redirect_url
                # Optional: We could change the status code to 200 to satisfy some proxies, 
                # but HX-Redirect works fine with 302 in most cases.
        
        return response
