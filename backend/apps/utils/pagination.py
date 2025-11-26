from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'message': 'OK',
            'data': data,
            'errors': None,
            'meta': {
                'count': self.page.paginator.count,
                'page': self.page.number,
                'pages': self.page.paginator.num_pages,
                'page_size': self.get_page_size(self.request),
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            }
        })