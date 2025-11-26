from django.db.models import Q

class QueryFilterHandler:
    """Dynamic filtering based on whitelisted fields.
    Usage: handler = QueryFilterHandler(query_params, ['email','username'])
           qs = handler.apply(User.objects.all())
    """
    def __init__(self, query_params, allowed_fields):
        self.query_params = query_params
        self.allowed_fields = allowed_fields

    def apply(self, queryset):
        filters = {}
        search_term = self.query_params.get('search')
        for field in self.allowed_fields:
            if field in self.query_params:
                filters[f"{field}__icontains"] = self.query_params[field]
        if filters:
            queryset = queryset.filter(**filters)
        if search_term:
            q_obj = Q()
            for field in self.allowed_fields:
                q_obj |= Q(**{f"{field}__icontains": search_term})
            queryset = queryset.filter(q_obj)
        return queryset