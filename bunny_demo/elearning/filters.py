from django_filters import filters, FilterSet

from .models import Course

class CourseFilter(FilterSet):

    name = filters.CharFilter(label='講座名', lookup_expr='contains')
    bunny_collection_id = filters.CharFilter(label='Collection Id', lookup_expr='contains')

    class Meta:
        model = Course
        fields = (
            'name',
            'bunny_collection_id',
        )