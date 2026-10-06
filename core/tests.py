from decimal import Decimal

from django.template import Context, Template
from django.test import TestCase


class HotelExtraFilterTests(TestCase):
    def test_multiply_converts_template_string_argument(self):
        rendered = Template(
            "{% load hotel_extras %}{{ rate|multiply:rooms|money }}"
        ).render(Context({"rate": Decimal("75.00"), "rooms": 2}))
        self.assertEqual(rendered, "$150.00")
