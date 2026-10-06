"""Cursor-free paginator helper that preserves active filters in page links."""
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(request, queryset, per_page: int = 25):
    params = request.GET.copy()
    params.pop("page", None)
    query = params.urlencode()
    query = f"{query}&" if query else ""
    paginator = Paginator(queryset, per_page)
    try:
        page = paginator.page(request.GET.get("page", 1))
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page, query
