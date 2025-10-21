from django.urls import path
from .views import StringsView, StringDetailView, NaturalLanguageFilterView

urlpatterns = [
    path("strings", StringsView.as_view(), name="strings"),
    path("strings/filter-by-natural-language", NaturalLanguageFilterView.as_view(), name="strings_nl"),
    path("strings/<path:string_value>", StringDetailView.as_view(), name="string_detail"),
]
