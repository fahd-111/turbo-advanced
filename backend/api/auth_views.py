from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST


@never_cache
@require_GET
def get_csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})


@never_cache
@require_POST
@csrf_protect
def login_user(request):
    form = AuthenticationForm(request, data=request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Invalid username or password."}, status=400)

    login(request, form.get_user())
    return JsonResponse({"status": "authenticated"})


@never_cache
@require_POST
@csrf_protect
def logout_user(request):
    logout(request)
    return JsonResponse({"status": "unauthenticated"})
