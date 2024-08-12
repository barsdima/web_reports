from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from reports.models import *

class ReportCreateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(username="test", password="test")

    def setUp(self):
        self.client.login(username="test", password="test")

    def test_view_accessible_by_name(self):
        response = self.client.get(reverse("submit_report"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("submit_report"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/submitreport.html")

    def test_redirect_when_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse("submit_report"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_post(self):
        pass

class ReportsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(username="test", password="test")

        environment_1 = Environment.objects.create(name="environment_1")
        environment_2 = Environment.objects.create(name="environment_2")
        environment_3 = Environment.objects.create(name="environment_3")

        testing_type_1 = TestingType.objects.create(name="test_1")
        testing_type_2 = TestingType.objects.create(name="test_2")
        testing_type_3 = TestingType.objects.create(name="test_3")

        Topic.objects.create(name="TOPIC")

        n_reports = 5
        data = {
            'form-TOTAL_FORMS': '4',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',

            'form-0-file_report': '',
            'form-0-name': 'a',
            'form-0-datapack': 'lan-COU-TOPIC-1.1.1',
            'form-0-testing_type': f"{testing_type_1.pk}",
            'form-0-environment': f"{environment_1.pk}",
            'form-0-link_QAServer': '',
            'form-0-jira': '',
            'form-0-notes': '',

            'form-1-file_report': '',
            'form-1-name': 'b',
            'form-1-datapack': 'lan-COU-TOPIC-1.1.1',
            'form-1-testing_type': f"{testing_type_2.pk}",
            'form-1-environment': f"{environment_2.pk}",
            'form-1-link_QAServer': '',
            'form-1-jira': '',
            'form-1-notes': '',

            'form-2-file_report': '',
            'form-2-name': 'c',
            'form-2-datapack': 'lan-COU-TOPIC-1.1.1',
            'form-2-testing_type': f"{testing_type_3.pk}",
            'form-2-environment': f"{environment_3.pk}",
            'form-2-link_QAServer': '',
            'form-2-jira': '',
            'form-2-notes': '',

            'form-3-file_report': '',
            'form-3-name': 'd',
            'form-3-datapack': 'abc-ABC-TOPIC-1.1.1',
            'form-3-testing_type': f"{testing_type_3.pk}",
            'form-3-environment': f"{environment_3.pk}",
            'form-3-link_QAServer': '',
            'form-3-jira': '',
            'form-3-notes': '',

            'form-4-file_report': '',
            'form-4-name': 'e',
            'form-4-datapack': 'abc-ABC-TOPIC-1.1.2',
            'form-4-testing_type': f"{testing_type_3.pk}",
            'form-4-environment': f"{environment_3.pk}",
            'form-4-link_QAServer': '',
            'form-4-jira': '',
            'form-4-notes': '',

            'tester': user
        }
        for i in range(n_reports):
            report = Report.create_new_report(object=data, prefix=f"form-{i}-")
            report.save()

    def test_objects_successfully_created(self):
        self.assertEqual(len(Report.objects.all()), 5)
        self.assertEqual(len(DataPack.objects.all()), 3)
        self.assertEqual(len(Language.objects.all()), 2)
        self.assertEqual(len(TestingType.objects.all()), 3)
        self.assertEqual(len(Environment.objects.all()), 3)
        self.assertEqual(len(Topic.objects.all()), 1)
        self.assertEqual(len(get_user_model().objects.all()), 1)

    def test_view_accessible_by_name(self):
        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/reports.html")

    def test_context_for_get_request(self):
        response = self.client.get(reverse("reports"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["compare"], False)
        self.assertEqual(len(response.context["reports"]), 5)

    def test_context_for_post_with_nothing_filtered(self):
        # simulate the clicking of the "filter" button, with nothing selected
        data = {
            'datapack': "",
            'language': "",
            'topic': "",
            'test_type': "",
            'environment': "",
            'tester': ""
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 5)
        self.assertEqual(response.context["compare"], False)

    def test_context_for_post_with_datapack_selected(self):
        data = {
            # datapack with id=1
            # should have 3 reports
            'datapack': "1",
            'language': "",
            'topic': "",
            'test_type': "",
            'environment': "",
            'tester': ""
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 3)
        self.assertEqual(response.context["compare"], False)

    def test_context_for_post_with_language_selected(self):
        data = {
            'datapack': "",
            'language': "1",
            'topic': "",
            'test_type': "",
            'environment': "",
            'tester': ""
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 3)
        self.assertEqual(response.context["compare"], False)

    def test_context_for_post_with_topic_selected(self):
        data = {
            'datapack': "",
            'language': "",
            'topic': "1",
            'test_type': "",
            'environment': "",
            'tester': ""
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 5)
        self.assertEqual(response.context["compare"], False)

    def test_context_for_post_with_testing_type_selected(self):
        data = {
            'datapack': "",
            'language': "",
            'topic': "",
            'test_type': "3",
            'environment': "",
            'tester': ""
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 3)
        self.assertEqual(response.context["compare"], False)

    def test_context_for_post_with_environment_selected(self):
        data = {
            'datapack': "",
            'language': "",
            'topic': "",
            'test_type': "",
            'environment': "3",
            'tester': ""
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 3)
        self.assertEqual(response.context["compare"], False)

    def test_context_for_post_with_tester_selected(self):
        data = {
            'datapack': "",
            'language': "",
            'topic': "",
            'test_type': "",
            'environment': "",
            'tester': "1"
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 5)
        self.assertEqual(response.context["compare"], False)

    def test_context_for_unsuccessful_comparison_diff_datapack_type(self):
        data = {
            'datapack': "",
            'language': "",
            'topic': "",
            'test_type': "",
            'environment': "",
            'tester': "",

            # compare report 3 and report 4
            # reports for the same testing type (testing_type_3), but different datapack types (lan-COU-TOPIC vs. abc-ABC-TOPIC)
            # should be unsuccessful
            "compare-3": "on",
            "compare-4": "on"
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 5)
        self.assertEqual(response.context["same_datapack_type"], False)

    def test_context_for_unsuccessful_comparison_diff_testing_type(self):
        data = {
            'datapack': "",
            'language': "",
            'topic': "",
            'test_type': "",
            'environment': "",
            'tester': "",

            # compare report 1 and report 2
            # reports for the same datapack type (lan-COU-TOPIC), but different testing types (testing_type_1 vs. testing_type_2)
            # should be unsuccessful
            "compare-1": "on",
            "compare-2": "on"
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 5)
        self.assertEqual(response.context["same_testing_type"], False)

    def test_context_for_unsuccessful_comparison_no_file(self):
        data = {
            'datapack': "",
            'language': "",
            'topic': "",
            'test_type': "",
            'environment': "",
            'tester': "",

            # compare report 4 and report 5
            # reports for the same datapack type (abc-ABC-TOPIC) and testing type
            # however, missing uploaded files
            # should be unsuccessful
            "compare-4": "on",
            "compare-5": "on"
        }
        response = self.client.post(reverse("reports"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["reports"]), 5)
        self.assertEqual(len(response.context["reports_missing_file"]), 2)

    # create a test case where the comparison is successful:
        # same datapack type
        # same testing type
        # all selected reports have a file

class DatapacksViewTest(TestCase):
    def test_view_accessible_by_name(self):
        response = self.client.get(reverse("dptracking"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dptracking"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/dptracking/tracking.html")

    def test_context_for_get_request(self):
        pass

    def test_post(self):
        pass

class LoginViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(username="test", password="test")

    def test_view_accessible_by_name(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/login.html")

class LogoutViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(username="test", password="test")

    def setUp(self):
        self.client.login(username="test", password="test")

    def test_view_accessible_by_name(self):
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, "/")

    def test_when_already_logged_out(self):
        self.client.logout()
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, "/")

# UpdateDatapackView, DeleteReportView, and ReportDetailView are generic Django views
