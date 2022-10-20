from .models import App


def appstats(request):
    return {
        "APPS": App.objects.all().order_by("name"),
    }
