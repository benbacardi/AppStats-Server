from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import make_aware

import json
from datetime import datetime

from jsonschema import validate, ValidationError

from .models import App, COUNTERS_SCHEMA, GAUGES_SCHEMA, EVENTS_SCHEMA


def home(request):
    return render(request, "appstats/home.html", {})


def app_home(request, app_slug):
    app = get_object_or_404(App, slug=app_slug)
    return render(request, "appstats/app_home.html", {
        "app": app,
        "by_model": app.active_installs_by_parameter("model"),
        "by_app_version": app.active_installs_by_parameter("app_version", "build_number"),
        "by_os_name": app.active_installs_by_parameter("os_name"),
        "by_os_version": app.active_installs_by_parameter("os_name", "os_version"),
    })


def counter(request, app_slug, counter_name):
    app = get_object_or_404(App, slug=app_slug)
    counter = get_object_or_404(app.counters, name=counter_name)
    return render(request, "appstats/counter.html", {
        "app": app,
        "counter": counter,
    })


def gauge(request, app_slug, gauge_name):
    app = get_object_or_404(App, slug=app_slug)
    gauge = get_object_or_404(app.gauges, name=gauge_name)
    return render(request, "appstats/gauge.html", {
        "app": app,
        "gauge": gauge,
    })


def event(request, app_slug, event_name):
    app = get_object_or_404(App, slug=app_slug)
    event = get_object_or_404(app.events, name=event_name)
    return render(request, "appstats/event.html", {
        "app": app,
        "event": event,
    })


@require_POST
@csrf_exempt
def register_counters(request, app_name):
    """Register a counter update."""

    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    try:
        validate(instance=data, schema=COUNTERS_SCHEMA)
    except ValidationError as err:
        return JsonResponse({"error": f"JSON does not match schema: {err.message}"}, status=400)

    try:
        app = App.objects.get(name=app_name, key=request.GET.get("key"))
    except App.DoesNotExist:
        return JsonResponse({"error": "Invalid app and key."}, status=401)

    results = []
    for counter in data["counters"]:
        results.append(app.register_counter(
            name=counter["name"],
            count=counter["count"],
            date_created=make_aware(datetime.fromtimestamp(counter["dateCreated"])),
            date_updated=make_aware(datetime.fromtimestamp(counter["dateUpdated"])),
            **data["device"],
        ))

    return JsonResponse({
        "success": "Counters updated.",
        "results": dict((x.counter.name, x.count) for x in results),
    })


@require_POST
@csrf_exempt
def register_gauges(request, app_name):
    """Register a Gauge value."""

    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    try:
        validate(instance=data, schema=GAUGES_SCHEMA)
    except ValidationError as err:
        return JsonResponse({"error": f"JSON does not match schema: {err.message}"}, status=400)

    try:
        app = App.objects.get(name=app_name, key=request.GET.get("key"))
    except App.DoesNotExist:
        return JsonResponse({"error": "Invalid app and key."}, status=401)

    results = []
    for gauge in data["gauges"]:
        results.append(app.register_gauge(
            name=gauge["name"],
            value=gauge["value"],
            date_created=make_aware(datetime.fromtimestamp(gauge["dateCreated"])),
            **data["device"],
        ))

    return JsonResponse({
        "success": "Gauges saved.",
        "results": dict((x.gauge.name, x.value) for x in results),
    })


@require_POST
@csrf_exempt
def register_events(request, app_name):
    """Register a counter update."""

    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    try:
        validate(instance=data, schema=EVENTS_SCHEMA)
    except ValidationError as err:
        return JsonResponse({"error": f"JSON does not match schema: {err.message}"}, status=400)

    try:
        app = App.objects.get(name=app_name, key=request.GET.get("key"))
    except App.DoesNotExist:
        return JsonResponse({"error": "Invalid app and key."}, status=401)

    results = []
    for event in data["events"]:
        results.append(app.register_event(
            name=event["name"],
            attributes=event.get("attributes", {}),
            date_created=make_aware(datetime.fromtimestamp(event["dateCreated"])),
            **data["device"],
        ))

    return JsonResponse({
        "success": "Events saved.",
        "results": dict((x.event.name, x.attributes) for x in results),
    })
