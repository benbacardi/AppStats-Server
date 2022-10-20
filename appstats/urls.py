from django.urls import path

from . import views


urlpatterns = [
    path("api/counters/<slug:app_name>/", views.register_counters),
    path("api/gauges/<slug:app_name>/", views.register_gauges),
    path("api/events/<slug:app_name>/", views.register_events),

    path("", views.home),
    path("app/<slug:app_slug>/", views.app_home, name="appstats.app_home"),
    path("app/<slug:app_slug>/counter/<str:counter_name>/", views.counter, name="appstats.counter"),
    path("app/<slug:app_slug>/gauge/<str:gauge_name>/", views.gauge, name="appstats.gauge"),
    path("app/<slug:app_slug>/event/<str:event_name>/", views.event, name="appstats.event"),
]
