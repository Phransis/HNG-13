from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import StringEntry
from .serializers import StringEntrySerializer, CreateStringSerializer
from . import utils

import logging

logger = logging.getLogger(__name__)

# Helpers
def build_properties(value: str) -> dict:
    sha = utils.sha256_hex(value)
    props = {
        "length": len(value),
        "is_palindrome": utils.is_palindrome(value),
        "unique_characters": utils.unique_characters(value),
        "word_count": utils.word_count(value),
        "sha256_hash": sha,
        "character_frequency_map": utils.character_frequency_map(value),
    }
    return props

def format_entry_response(entry: StringEntry) -> dict:
    return {
        "id": entry.id,
        "value": entry.value,
        "properties": entry.properties,
        "created_at": entry.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    }

# POST /strings and GET /strings (list with filters)
class StringsView(APIView):
    def post(self, request):
        serializer = CreateStringSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": "Invalid request body or missing 'value' field"}, status=status.HTTP_400_BAD_REQUEST)

        value = serializer.validated_data["value"]

        if not isinstance(value, str):
            return Response({"detail": "Invalid data type for 'value' (must be string)"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        sha = utils.sha256_hex(value)
        if StringEntry.objects.filter(id=sha).exists():
            return Response({"detail": "String already exists in the system"}, status=status.HTTP_409_CONFLICT)

        props = build_properties(value)
        entry = StringEntry.objects.create(id=sha, value=value, properties=props)
        resp = format_entry_response(entry)
        return Response(resp, status=status.HTTP_201_CREATED)

    def get(self, request):
        # Supported filters:
        # is_palindrome (true/false), min_length, max_length, word_count, contains_character
        qs = StringEntry.objects.all()
        qp = request.query_params

        filters_applied = {}

        # is_palindrome
        is_pal = qp.get("is_palindrome")
        if is_pal is not None:
            if is_pal.lower() not in ("true", "false"):
                return Response({"detail": "Invalid is_palindrome value"}, status=status.HTTP_400_BAD_REQUEST)
            bool_val = is_pal.lower() == "true"
            qs = qs.filter(properties__is_palindrome=bool_val)
            filters_applied["is_palindrome"] = bool_val

        # min_length
        min_len = qp.get("min_length")
        if min_len is not None:
            try:
                mi = int(min_len)
            except ValueError:
                return Response({"detail": "Invalid min_length"}, status=status.HTTP_400_BAD_REQUEST)
            qs = qs.filter(properties__length__gte=mi)
            filters_applied["min_length"] = mi

        # max_length
        max_len = qp.get("max_length")
        if max_len is not None:
            try:
                ma = int(max_len)
            except ValueError:
                return Response({"detail": "Invalid max_length"}, status=status.HTTP_400_BAD_REQUEST)
            qs = qs.filter(properties__length__lte=ma)
            filters_applied["max_length"] = ma

        # word_count exact
        wc = qp.get("word_count")
        if wc is not None:
            try:
                wci = int(wc)
            except ValueError:
                return Response({"detail": "Invalid word_count"}, status=status.HTTP_400_BAD_REQUEST)
            qs = qs.filter(properties__word_count=wci)
            filters_applied["word_count"] = wci

        # contains_character - case-sensitive search in value
        cc = qp.get("contains_character")
        if cc is not None:
            if len(cc) != 1:
                return Response({"detail": "contains_character must be a single character"}, status=status.HTTP_400_BAD_REQUEST)
            qs = qs.filter(value__contains=cc)
            filters_applied["contains_character"] = cc

        entries = [format_entry_response(e) for e in qs.order_by("-created_at")]
        return Response({
            "data": entries,
            "count": len(entries),
            "filters_applied": filters_applied
        }, status=status.HTTP_200_OK)


# GET /strings/{string_value} and DELETE
class StringDetailView(APIView):
    def get_entry_by_value_or_404(self, value):
        sha = utils.sha256_hex(value)
        return get_object_or_404(StringEntry, id=sha)

    def get(self, request, string_value):
        entry = self.get_entry_by_value_or_404(string_value)
        return Response(format_entry_response(entry), status=status.HTTP_200_OK)

    def delete(self, request, string_value):
        sha = utils.sha256_hex(string_value)
        try:
            entry = StringEntry.objects.get(id=sha)
        except StringEntry.DoesNotExist:
            return Response({"detail": "String does not exist in the system"}, status=status.HTTP_404_NOT_FOUND)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Natural language filtering: GET /strings/filter-by-natural-language?query=...
class NaturalLanguageFilterView(APIView):
    """
    Very lightweight NLP: use keywords to create filters.
    Supported heuristics (examples in spec):
     - "single word" -> word_count=1
     - "palindromic" or "palindrome" -> is_palindrome=true
     - "strings longer than N characters" -> min_length=N+1
     - "strings containing the letter z" -> contains_character=z
     - "contain the first vowel" -> contains_character=a (heuristic)
    """
    def parse_query(self, q: str):
        if not q:
            raise ValueError("Empty query")

        ql = q.lower()
        parsed = {}

        if "single word" in ql:
            parsed["word_count"] = 1

        if "palindrom" in ql:
            parsed["is_palindrome"] = True

        # longer than N characters
        import re
        m = re.search(r"longer than (\d+) characters", ql)
        if m:
            n = int(m.group(1))
            parsed["min_length"] = n + 1

        # strings longer than 10 -> also support "longer than 10"
        m2 = re.search(r"longer than (\d+)", ql)
        if m2 and "min_length" not in parsed:
            n = int(m2.group(1))
            parsed["min_length"] = n + 1

        # contain the letter X
        m3 = re.search(r"letter\s+([a-z])", ql)
        if m3:
            parsed["contains_character"] = m3.group(1)

        # contains 'z' pattern
        m4 = re.search(r"containing the letter\s+([a-z])", ql)
        if m4:
            parsed["contains_character"] = m4.group(1)

        # contains the first vowel -> heuristic 'a'
        if "first vowel" in ql or "contains the first vowel" in ql:
            parsed["contains_character"] = parsed.get("contains_character", "a")

        if not parsed:
            raise ValueError("Unable to parse natural language query")

        return parsed

    def get(self, request):
        q = request.query_params.get("query")
        try:
            parsed = self.parse_query(q)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Now reuse the list filtering logic by constructing a query string and calling StringsView
        # We'll apply filters directly here (similar logic as StringsView.get)
        qs = StringEntry.objects.all()
        if "is_palindrome" in parsed:
            qs = qs.filter(properties__is_palindrome=parsed["is_palindrome"])
        if "min_length" in parsed:
            qs = qs.filter(properties__length__gte=parsed["min_length"])
        if "max_length" in parsed:
            qs = qs.filter(properties__length__lte=parsed["max_length"])
        if "word_count" in parsed:
            qs = qs.filter(properties__word_count=parsed["word_count"])
        if "contains_character" in parsed:
            cc = parsed["contains_character"]
            if len(cc) != 1:
                return Response({"detail": "Invalid contains_character parsed"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            qs = qs.filter(value__contains=cc)

        entries = [format_entry_response(e) for e in qs.order_by("-created_at")]
        return Response({
            "data": entries,
            "count": len(entries),
            "interpreted_query": {
                "original": q,
                "parsed_filters": parsed
            }
        }, status=status.HTTP_200_OK)
