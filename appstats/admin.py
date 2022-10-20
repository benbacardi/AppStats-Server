from django.contrib import admin

from .models import App, Counter, Gauge, Event, Install, InstalledVersion, CounterInstance, GaugeInstance, EventInstance


class AppAdmin(admin.ModelAdmin):
    list_display = ("name", "installs", "active_installs")
    prepopulated_fields = {"slug": ("name",)}

    def installs(self, obj):
        return obj.installs.count()

    def active_installs(self, obj):
        return obj.active_installs().count()


class MetricAdmin(admin.ModelAdmin):
    list_display = ("name", "app")
    list_filter = ("app",)
    search_fields = ("name",)


class InstallAdmin(admin.ModelAdmin):
    list_display = ("device_id", "app", "date_created", "date_updated")
    list_filter = ("app",)
    search_fields = ("device_id",)


class VersionAdmin(admin.ModelAdmin):
    list_display = ("device_id", "model", "app_version", "build_number", "os_name", "os_version", "os_version_string", "date_created")
    list_filter = ("os_name", "os_version", "model", "install__app")
    search_fields = ("os_name", "os_version", "model", "app_version", "build_number",)

    def device_id(self, obj):
        return obj.install.device_id


class InstanceModelMixin:

    def install_os(self, obj):
        return obj.version.os_version_string

    def install_model(self, obj):
        return obj.version.model


class CounterAdmin(InstanceModelMixin, admin.ModelAdmin):
    list_display = ("name", "app", "install_os", "install_model", "count", "date_created", "date_updated")
    list_filter = ("counter__app", "version__os_version_string", "counter")
    search_fields = ("counter__name",)

    def app(self, obj):
        return obj.counter.app

    def name(self, obj):
        return obj.counter.name


class GaugeAdmin(InstanceModelMixin, admin.ModelAdmin):
    list_display = ("name", "app", "install_os", "install_model", "value", "date_created")
    list_filter = ("gauge__app", "version__os_version_string", "gauge")
    search_fields = ("gauge__name",)

    def app(self, obj):
        return obj.gauge.app

    def name(self, obj):
        return obj.gauge.name


class EventAdmin(InstanceModelMixin, admin.ModelAdmin):
    list_display = ("name", "app", "install_os", "install_model", "date_created")
    list_filter = ("event__app", "version__os_version_string", "event")
    search_fields = ("event__name",)

    def app(self, obj):
        return obj.event.app

    def name(self, obj):
        return obj.event.name


admin.site.register(App, AppAdmin)
admin.site.register(Counter, MetricAdmin)
admin.site.register(Gauge, MetricAdmin)
admin.site.register(Event, MetricAdmin)
admin.site.register(Install, InstallAdmin)
admin.site.register(InstalledVersion, VersionAdmin)
admin.site.register(CounterInstance, CounterAdmin)
admin.site.register(GaugeInstance, GaugeAdmin)
admin.site.register(EventInstance, EventAdmin)
