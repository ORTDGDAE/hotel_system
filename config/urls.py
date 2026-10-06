from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("auth/", include("accounts.urls")),
    path("rooms/", include("hotel.urls")),
    path("hotels/", include("hotel.collection_urls")),
    path("bookings/", include("bookings.urls")),
    path("operations/", include("operations.urls")),
    path("finance/", include("finance.urls")),
    path("analytics/", include("analytics.urls")),
    path("pms/", include("bookings.pms_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Aurelia Grand · Administration"
admin.site.site_title = "Aurelia Grand Admin"
admin.site.index_title = "Property management"
