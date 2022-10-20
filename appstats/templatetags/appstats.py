from django import template

from ..model_mapping import MODEL_MAPPINGS

register = template.Library()


@register.filter
def verbose_model_name(name):
    return MODEL_MAPPINGS.get(name, name)


@register.filter
def sort_by_value(mapping):
    return sorted(mapping.items(), key=lambda x: -x[1])
