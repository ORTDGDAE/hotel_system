import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from hotel.models import Property, Room, RoomType

from .models import HousekeepingTask


class RoomStreamTests(TestCase):
    """Regression coverage for the live room-board SSE contract."""

    def setUp(self):
        self.property = Property.objects.create(name="Stream Test Hotel", city="Phnom Penh")
        room_type = RoomType.objects.create(
            property=self.property,
            name="Stream Test Room",
            base_price="100.00",
            total_rooms=1,
        )
        self.room = Room.objects.create(
            room_type=room_type,
            number="101",
            floor=1,
            status=Room.Status.VACANT_CLEAN,
        )
        other_property = Property.objects.create(name="Other Stream Hotel", city="Siem Reap")
        other_type = RoomType.objects.create(
            property=other_property,
            name="Other Stream Room",
            base_price="110.00",
            total_rooms=1,
        )
        Room.objects.create(
            room_type=other_type,
            number="201",
            floor=2,
            status=Room.Status.MAINTENANCE,
        )
        User = get_user_model()
        self.user = User.objects.create_user(
            username="stream-admin",
            password="test-password-123",
            role=User.Role.ADMIN,
        )
        self.client.force_login(self.user)
        session = self.client.session
        session["pms_active_property"] = self.property.pk
        session.save()

    def test_initial_event_is_json_serializable_and_scoped(self):
        response = self.client.get(reverse("operations:room_stream"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/event-stream")

        try:
            chunk = next(iter(response.streaming_content)).decode()
        finally:
            response.close()

        self.assertTrue(chunk.startswith("data: "))
        payload = json.loads(chunk.removeprefix("data: ").strip())
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], self.room.pk)
        self.assertEqual(payload[0]["status"], Room.Status.VACANT_CLEAN)
        self.assertEqual(payload[0]["tone"], "success")


class HousekeepingAssignmentTests(TestCase):
    def setUp(self):
        self.property = Property.objects.create(name="Assignment Test Hotel", city="Phnom Penh")
        room_type = RoomType.objects.create(
            property=self.property,
            name="Assignment Test Room",
            base_price="100.00",
            total_rooms=1,
        )
        self.room = Room.objects.create(
            room_type=room_type,
            number="301",
            floor=3,
            status=Room.Status.VACANT_DIRTY,
        )
        User = get_user_model()
        self.manager = User.objects.create_user(
            username="assignment-manager", password="test-password-123", role=User.Role.MANAGER,
            home_property=self.property,
        )
        self.housekeeper = User.objects.create_user(
            username="assignment-housekeeper", password="test-password-123", role=User.Role.HOUSEKEEPING,
            home_property=self.property,
        )
        self.other_housekeeper = User.objects.create_user(
            username="other-housekeeper", password="test-password-123", role=User.Role.HOUSEKEEPING,
            home_property=self.property,
        )
        self.reception = User.objects.create_user(
            username="assignment-reception", password="test-password-123", role=User.Role.RECEPTIONIST,
            home_property=self.property,
        )
        session = self.client.session
        session["pms_active_property"] = self.property.pk
        session.save()

    def make_task(self, assigned_to=None, status=HousekeepingTask.Status.PENDING):
        return HousekeepingTask.objects.create(
            room=self.room,
            task_type=HousekeepingTask.TaskType.CHECKOUT_CLEAN,
            priority=HousekeepingTask.Priority.HIGH,
            status=status,
            assigned_to=assigned_to,
        )

    def test_dirty_room_status_creates_one_open_cleaning_task(self):
        self.room.status = Room.Status.VACANT_CLEAN
        self.room.save(update_fields=["status", "updated_at"])
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("operations:room_status", args=[self.room.pk]),
            {"status": Room.Status.VACANT_DIRTY},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.room.housekeeping_tasks.filter(status=HousekeepingTask.Status.PENDING).count(), 1)
        task = self.room.housekeeping_tasks.get()
        self.assertEqual(task.task_type, HousekeepingTask.TaskType.CHECKOUT_CLEAN)
        self.assertEqual(task.priority, HousekeepingTask.Priority.URGENT)
        self.assertIsNone(task.assigned_to_id)

        # Repeating a dirty status update reuses the same workflow card.
        self.client.post(
            reverse("operations:room_status", args=[self.room.pk]),
            {"status": Room.Status.VACANT_DIRTY},
        )
        self.assertEqual(self.room.housekeeping_tasks.filter(status=HousekeepingTask.Status.PENDING).count(), 1)

        board = self.client.get(reverse("operations:room_board"))
        self.assertContains(board, "Cleaning: Pending")
        self.assertContains(board, "Needs assignment")

    def test_manager_can_assign_housekeeping_task(self):
        task = self.make_task()
        self.client.force_login(self.manager)
        response = self.client.post(reverse("operations:task_assign", args=[task.pk]), {"assigned_to": self.housekeeper.pk})
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.assigned_to_id, self.housekeeper.pk)

    def test_housekeeper_can_start_only_an_assigned_task(self):
        task = self.make_task(assigned_to=self.housekeeper)
        self.client.force_login(self.housekeeper)
        response = self.client.post(reverse("operations:task_start", args=[task.pk]))
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, HousekeepingTask.Status.IN_PROGRESS)
        self.assertEqual(task.assigned_to_id, self.housekeeper.pk)

    def test_housekeeper_cannot_claim_unassigned_task(self):
        task = self.make_task()
        self.client.force_login(self.housekeeper)
        response = self.client.post(reverse("operations:task_start", args=[task.pk]))
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, HousekeepingTask.Status.PENDING)
        self.assertIsNone(task.assigned_to_id)

    def test_housekeeper_cannot_operate_task_assigned_to_someone_else(self):
        task = self.make_task(assigned_to=self.other_housekeeper)
        self.client.force_login(self.housekeeper)
        response = self.client.post(reverse("operations:task_complete", args=[task.pk]))
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, HousekeepingTask.Status.PENDING)
        self.assertEqual(task.assigned_to_id, self.other_housekeeper.pk)

    def test_reception_is_view_only_for_housekeeping_assignment(self):
        task = self.make_task()
        self.client.force_login(self.reception)
        response = self.client.post(reverse("operations:task_assign", args=[task.pk]), {"assigned_to": self.housekeeper.pk})
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertIsNone(task.assigned_to_id)

    def test_housekeeper_sees_only_assigned_work_and_not_management_pages(self):
        own = self.make_task(assigned_to=self.housekeeper)
        self.make_task(assigned_to=self.other_housekeeper)
        self.client.force_login(self.housekeeper)

        board = self.client.get(reverse("operations:task_board"))
        self.assertEqual(board.status_code, 200)
        self.assertEqual({task.pk for task in board.context["pending"]}, {own.pk})
        self.assertContains(board, "My Housekeeping Tasks")
        self.assertNotContains(board, "> Dashboard</a>")

        dashboard = self.client.get(reverse("pms:dashboard"))
        self.assertRedirects(dashboard, reverse("operations:task_board"), fetch_redirect_response=False)
        room_board = self.client.get(reverse("operations:room_board"))
        self.assertRedirects(room_board, reverse("operations:task_board"), fetch_redirect_response=False)
