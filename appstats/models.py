import datetime

from django.db import models
from django.utils import timezone


DEVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "device_id": {"type": "string"},
        "model": {"type": "string"},
        "app_version": {"type": "string"},
        "build_number": {"type": "string"},
        "os_name": {"type": "string"},
        "os_version": {"type": "string"},
        "os_version_string": {"type": "string"},
    },
    "required": [
        "device_id",
        "model",
        "app_version",
        "build_number",
        "os_name",
        "os_version",
        "os_version_string",
    ]
}

COUNTER_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer"},
        "dateCreated": {"type": "integer"},
        "dateUpdated": {"type": "integer"},
    },
    "required": ["name", "count", "dateCreated", "dateUpdated"],
}

GAUGE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "value": {"type": "number"},
        "dateCreated": {"type": "integer"},
    },
    "required": ["name", "value", "dateCreated"],
}

EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "attributes": {"oneOf": [{"type": "object"}, {"type": "null"}]},
        "dateCreated": {"type": "integer"},
    },
    "required": ["name", "dateCreated"],
}

COUNTERS_SCHEMA = {
    "type": "object",
    "properties": {
        "counters": {"type": "array", "items": COUNTER_SCHEMA},
        "device": DEVICE_SCHEMA,
    },
    "required": ["counters", "device"],
}

GAUGES_SCHEMA = {
    "type": "object",
    "properties": {
        "gauges": {"type": "array", "items": GAUGE_SCHEMA},
        "device": DEVICE_SCHEMA,
    },
    "required": ["gauges", "device"],
}

EVENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {"type": "array", "items": EVENT_SCHEMA},
        "device": DEVICE_SCHEMA,
    },
    "required": ["events", "device"],
}


class App(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True)
    key = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def active_installs(self):
        return self.installs.filter(date_updated__gte=timezone.now() - datetime.timedelta(days=60))

    def active_install_versions(self):
        return InstalledVersion.objects.filter(install__in=self.active_installs(), latest=True)

    def active_installs_by_parameter(self, *parameters):
        return self.active_install_versions().values(*parameters).annotate(total=models.Count("install")).order_by("-total")

    def active_count_per_model(self):
        return {x["model"]: x["total"] for x in self.active_installs_by_parameter("model")}

    def active_count_per_os_name(self):
        return {x["os_name"]: x["total"] for x in self.active_installs_by_parameter("os_name")}

    def active_count_per_os_version(self):
        return {(x["os_name"], x["os_version"]): x["total"] for x in self.active_installs_by_parameter("os_name", "os_version")}

    def active_count_per_app_version(self):
        return {(x["app_version"], x["build_number"]): x["total"] for x in self.active_installs_by_parameter("app_version", "build_number")}

    def register_instance(self, device_id, model, app_version, build_number, os_name, os_version, os_version_string, **kwargs):
        install, _created = self.installs.get_or_create(
            device_id=device_id,
        )
        version, _created = install.versions.get_or_create(
            model=model,
            app_version=app_version,
            build_number=build_number,
            os_name=os_name,
            os_version=os_version,
            os_version_string=os_version_string,
        )
        version.latest = True
        version.save()
        install.versions.exclude(pk=version.pk).update(latest=False)
        return (install, version)

    def register_counter(self, name, count, date_created, date_updated, **kwargs):
        install, version = self.register_instance(**kwargs)
        counter, _created = self.counters.get_or_create(name=name)
        counter_instance, _created = counter.instances.get_or_create(
            install=install,
            version=version,
            defaults={
                "date_created": date_created,
                "date_updated": date_updated,
            })
        counter_instance.count += count
        if date_updated > counter_instance.date_updated:
            counter_instance.date_updated = date_updated
        counter_instance.save()
        return counter_instance

    def register_gauge(self, name, value, date_created=None, **kwargs):
        install, version = self.register_instance(**kwargs)
        gauge, _created = self.gauges.get_or_create(name=name)
        gauge_instance = GaugeInstance(
            gauge=gauge,
            install=install,
            version=version,
            value=value,
            date_created=date_created,
        )
        gauge_instance.save()
        return gauge_instance

    def register_event(self, name, attributes, date_created=None, **kwargs):
        install, version = self.register_instance(**kwargs)
        event, _created = self.events.get_or_create(name=name)
        event_instance = EventInstance(
            event=event,
            install=install,
            version=version,
            attributes=attributes,
            date_created=date_created,
        )
        event_instance.save()
        return event_instance


class MetricMixin:

    def active_instances(self):
        return self.instances.filter(
            install__in=self.app.active_installs()
        )

    def active_count_per_parameter(self, *parameters):
        active_items = self.active_instances().values_list(*parameters).distinct()
        results = {}
        for items in active_items:
            kwargs = {p: i for p, i in zip(parameters, items)}
            results[items[0] if len(items) == 1 else items] = self._count(self.active_instances().filter(**kwargs))
        return results

    def active_count_per_model(self):
        return self.active_count_per_parameter("version__model")

    def active_count_per_os_name(self):
        return self.active_count_per_parameter("version__os_name")

    def active_count_per_os_version(self):
        return self.active_count_per_parameter("version__os_name", "version__os_version")

    def active_count_per_app_version(self):
        return self.active_count_per_parameter("version__app_version", "version__build_number")


class Counter(MetricMixin, models.Model):
    app = models.ForeignKey(App, related_name="counters", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.app.name}: Counter {self.name}"

    class Meta:
        unique_together = (("name", "app",))

    def _count(self, queryset):
        return queryset.aggregate(models.Sum("count"))["count__sum"]

    def total(self):
        return self.active_instances().aggregate(models.Sum("count"))["count__sum"]


class Gauge(MetricMixin, models.Model):
    app = models.ForeignKey(App, related_name="gauges", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.app.name}: Gauge {self.name}"

    class Meta:
        unique_together = (("name", "app",))

    def _count(self, queryset):
        return queryset.count()

    def total(self):
        return self.instances.filter(install__in=self.app.active_installs()).count()


class Event(MetricMixin, models.Model):
    app = models.ForeignKey(App, related_name="events", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.app.name}: Event {self.name}"

    class Meta:
        unique_together = (("name", "app",))

    def _count(self, queryset):
        return queryset.count()

    def total(self):
        return self.instances.filter(install__in=self.app.active_installs()).count()


class Install(models.Model):
    app = models.ForeignKey(App, related_name="installs", on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.app.name}: Install {self.device_id}"


class InstalledVersion(models.Model):
    install = models.ForeignKey(Install, related_name="versions", on_delete=models.CASCADE)
    model = models.CharField(max_length=255)
    app_version = models.CharField(max_length=255)
    build_number = models.CharField(max_length=255)
    os_name = models.CharField(max_length=255)
    os_version = models.CharField(max_length=255)
    os_version_string = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True)
    latest = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.install.app.name}: Install {self.install.device_id} ({self.model}) - Version {self.app_version} ({self.build_number}) on {self.os_name} {self.os_version}"


class CounterInstance(models.Model):
    counter = models.ForeignKey(Counter, related_name="instances", on_delete=models.CASCADE)
    install = models.ForeignKey(Install, related_name="counters", on_delete=models.CASCADE)
    version = models.ForeignKey(InstalledVersion, related_name="counters", on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    date_created = models.DateTimeField()
    date_updated = models.DateTimeField()

    def __str__(self):
        return f"{self.counter.app.name}: Install {self.install.device_id}: Counter {self.counter.name}: {self.count}"


class GaugeInstance(models.Model):
    gauge = models.ForeignKey(Gauge, related_name="instances", on_delete=models.CASCADE)
    install = models.ForeignKey(Install, related_name="gauges", on_delete=models.CASCADE)
    version = models.ForeignKey(InstalledVersion, related_name="gauges", on_delete=models.CASCADE)
    value = models.FloatField()
    date_created = models.DateTimeField()

    def __str__(self):
        return f"{self.gauge.app.name}: Install {self.install.device_id}: Gauge {self.gauge.name}: {self.date_created}"


class EventInstance(models.Model):
    event = models.ForeignKey(Event, related_name="instances", on_delete=models.CASCADE)
    install = models.ForeignKey(Install, related_name="events", on_delete=models.CASCADE)
    version = models.ForeignKey(InstalledVersion, related_name="events", on_delete=models.CASCADE)
    attributes = models.JSONField(blank=True, null=True)
    date_created = models.DateTimeField()

    def __str__(self):
        return f"{self.event.app.name}: Install {self.install.device_id}: Event {self.event.name}: {self.date_created}"
