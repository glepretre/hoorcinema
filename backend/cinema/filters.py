from django.db.models import F
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend, OrderingFilter


class ExactChoiceFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        for field_name in view.choice_filter_fields:
            value = request.query_params.get(field_name)
            if value is None:
                continue

            choices = dict(queryset.model._meta.get_field(field_name).choices)
            if value not in choices:
                raise ValidationError(
                    {field_name: [f'"{value}" is not a valid choice.']}
                )
            queryset = queryset.filter(**{field_name: value})

        return queryset


class NullsLastOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset

        expressions = []
        for field_name in ordering:
            if field_name.startswith("-"):
                expressions.append(F(field_name[1:]).desc(nulls_last=True))
            else:
                expressions.append(F(field_name).asc(nulls_last=True))
        return queryset.order_by(*expressions)
