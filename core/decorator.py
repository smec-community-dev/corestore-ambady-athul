from django.http import HttpResponse
from functools import wraps

def seller_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse("Unauthorized", status=401)
        if request.user.role != 'seller':
            return HttpResponse("Forbidden", status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view