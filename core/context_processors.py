from .models import UserSettings

def user_theme(request):
    if request.user.is_authenticated:
        try:
            settings = request.user.settings
            return {'user_theme': settings.theme_preference}
        except UserSettings.DoesNotExist:
            UserSettings.objects.create(user=request.user)
            return {'user_theme': 'light'}
    else:
        return {'user_theme': 'light'}