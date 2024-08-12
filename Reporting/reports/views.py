import copy
import json
import os
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.views import View

import reports.utils.backend as backend
from reports.utils.forms import (
    ReportFiltersForm,
    SubmitreportForm,
    DatapackFiltersForm
)
from reports.models import Report, TestingType, Environment, DataPack
from reports.utils.forms import SubmitreportFormSet, UpdateReportForm, UpdateDatapackForm
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime
from django.db.utils import DataError
from reports.utils.compare import compare_accuracy, compare_travel_corpus, compare_NTE5, compare_load, compare_load_advanced, dict_to_str

class ReportsView(View):
    def get(self, request):
        """
        Displays the 100 latest reports
        """
        reports = Report.objects.order_by("-id")[:100]
        filter_form = ReportFiltersForm()
        return render(
            request, "reports/reports.html", {
                "reports": reports,
                "filter_form": filter_form,
                "compare": False,
            }
        )

    def post(self, request):
        """
        Handles report filtering and/or comparison of selected reports
        """
        # filter reports by the selected filters
        filter_form = ReportFiltersForm(request.POST)
        reports = Report.objects.all().order_by("-id")
        if filter_form.is_valid():
            for changedata in filter_form.changed_data:
                if changedata == "topic":
                    reports = reports.filter(
                        datapack__topic=filter_form.cleaned_data["topic"]
                    )
                if changedata == "language":
                    reports = reports.filter(
                        datapack__language=filter_form.cleaned_data["language"]
                    )
                if changedata == "datapack":
                    reports = reports.filter(
                        datapack=filter_form.cleaned_data["datapack"]
                    )
                if changedata == "tester":
                    reports = reports.filter(
                        tester=filter_form.cleaned_data["tester"]
                    )
                if changedata == "test_type":
                    reports = reports.filter(
                        testing_type=filter_form.cleaned_data["test_type"]
                    )
                if changedata == "environment":
                    reports = reports.filter(
                        environment=filter_form.cleaned_data["environment"]
                    )

        # get the reports that the user selected (selected checkboxes)
        to_compare = []
        for field in request.POST:
            # in reports.html:
            # "<td><input type="checkbox" name="compare-{{ report.id }}" /></td>"
            # get the selected reports based on the report.id parsed from the "compare-{{ report.id }}"
            # field in request.POST
            if "compare" in field:
                _, report_id = field.split("-")
                to_compare.append(Report.objects.get(id=report_id))

        # determines if the user wants to do a comparison (reports were selected for comparison)
        if to_compare:
            def get_datapack_type(name):
                """
                Returns the datapack name with the version stripped off
                """
                language, country, topic, version = name.split("-")
                return f"{language}-{country}-{topic}"

            # e.g. fra-FRA-GEN-4.0.0 and fra-FRA-GEN-4.1.0 both have the same type: fra-FRA-GEN
            unique_datapack_types = set([get_datapack_type(report.datapack.name) for report in to_compare])
            # check if all the reports are for the same datapack type
            # this is because we want to make sure that the user wants to compare report(s) for the same datapack type
            # e.g. cannot compare one report for eng-USA-GEN and another for fra-FRA-GEN
            same_datapack_type = True if len(unique_datapack_types) == 1 else False
            if not same_datapack_type:
                return render(
                    request, "reports/reports.html", {
                        "reports": reports,
                        "filter_form": filter_form,
                        "same_datapack_type": False,
                    }
                )

            # check if all the reports are for the same testing type
            # e.g. cannot compare an accuracy test result with a travel corpus test result
            types_arr = [report.testing_type.name for report in to_compare]
            is_travel_corpus_comp = True
            for tt in types_arr:
                if "TravelCorpus" not in tt:
                    is_travel_corpus_comp = False
                    break

            unique_testing_types = set(types_arr)
            same_testing_type = True if len(unique_testing_types) == 1 or is_travel_corpus_comp else False
            if not same_testing_type:
                return render(
                    request, "reports/reports.html", {
                        "reports": reports,
                        "filter_form": filter_form,
                        "same_testing_type": False,
                    }
                )

            # get the test result files (file uploaded during report submission) for the selected reports
            report_files = [(report, report.file_report) for report in to_compare]

            # determine if all the selected reports have a test result file
            reports_missing_file = []
            for report, file in report_files:
                if not file:
                    reports_missing_file.append(report)

            if reports_missing_file:
                return render(
                    request, "reports/reports.html", {
                        "reports": reports,
                        "filter_form": filter_form,
                        "reports_missing_file": reports_missing_file,
                    }
                )

            # at this point, we know the following:
            # 1. all the selected reports are for the same datapack type (e.g. eng-USA-GEN)
            # 2. all the selected reports are for the same testing type (e.g. accuracy 8k)
            # 3. all the selected reports have a test result file that was uploaded during submission

            comparison_result = []
            # get the testing type
            testing_type = unique_testing_types.pop()
            table_title = testing_type
            if len(set(types_arr)) > 1:
                table_title = f"{types_arr[0]} vs. {types_arr[1]}"
            # different testing types test different things, and thus produce different result files
            # this means that the comparison of accuracy test results
            # is handled differently from the comparison of travel corpus test results
            # please refer to utils/compare.py to see how all the different comparisons are handled
            if testing_type == "MIX_accuracy_test_8k" or testing_type == "MIX_accuracy_test_16k" or testing_type == "NES_accuracy_test_8k":
                comparison_result = compare_accuracy(to_compare)
            if testing_type == "NTE5":
                comparison_result = compare_NTE5(to_compare)
            if (
                    testing_type == "FAST_DNN_TravelCorpus" or
                    testing_type == "DNN_TravelCorpus" or
                    testing_type == "MIX_TravelCorpus_2.15" or
                    testing_type == "MIX_TravelCorpus_2.22" or
                    testing_type == "NLE_NES_TravelCorpus"
            ):
                comparison_result = compare_travel_corpus(to_compare)
            if testing_type == "load_test":
                comparison_result = compare_load_advanced(to_compare, True)

            return render(
                request, "reports/reports.html", {
                    "reports": reports,
                    "filter_form": filter_form,
                    "testing_type": testing_type,
                    "table_title": table_title,
                    "comparison_result": comparison_result,
                    "to_compare": to_compare,
                }
            )

        return render(
            request, "reports/reports.html", {
                "reports": reports,
                "filter_form": filter_form,
                "compare": False,
            }
        )


class ReportDetailView(DetailView):
    model = Report
    context_object_name = "report"
    template_name = "reports/reportdetail.html"


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = SubmitreportForm
    template_name = "reports/submitreport.html"
    context_object_name = "form"
    login_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            testing_types = (
                TestingType.objects.all().exclude(name__exact="").order_by("name")
            )
            environments = (
                Environment.objects.filter(name__isnull=False)
                .exclude(name__exact="")
                .order_by("name")
            )
        except Exception as err:
            pass
        finally:
            context["from_db"] = {
                "testing_types": testing_types,
                "environments": environments,
            }
            context["formset"] = SubmitreportFormSet()
        return context

    def post(self, request, *args, **kwargs) -> HttpResponse:
        data = {**dict(request.POST), **dict(request.FILES)}
        for field in data.keys():  # convert array values to str
            data[field] = data[field][0]
        data["tester"] = request.user

        total_form = int(data.get("form-TOTAL_FORMS"))
        try:
            saved_reports = []
            for i in range(total_form):
                report = Report.create_new_report(data, prefix=f"form-{i}-")
                if type(report) == Report:
                    try:
                        report.save()
                    except DataError:
                        pass # ignore the "Data too long for column 'file_report'" error and continue
                    saved_reports.append({"report": report.name, "status": "Success"})
                else:
                    saved_reports.append(
                        {"report": report.get("report"), "status": report.get("error")}
                    )
            return render(
                request, "reports/submitreportresult.html", {"summary": saved_reports}
            )
        except Exception as err:
            return HttpResponse(str(err))


# this is currently non-functional
@csrf_exempt
def submit_report_api(request):
    if request.method == "GET":
        return HttpResponse("Submit Report API")
    elif request.method == "POST":
        res = HttpResponse("")
        try:
            data = copy.deepcopy(json.loads(request.body))
            data["file_report"] = request.FILES.get("file")
            try:
                data["parameters"] = backend.getParameterINI(data.get("link_QAServer"))
            except:
                data["parameters"] = ""

            report = Report.create_new_report(data)
            if type(report) == Report:
                report.save()
                res = HttpResponse("Upload Successful! ", report)
            else:
                res = HttpResponse(report.get("error"))
        except Exception as err:
            print(err)
            res = HttpResponse(str(err))
        finally:
            return res

class UpdateReportView(LoginRequiredMixin, UpdateView):
    model = Report
    form_class = UpdateReportForm
    context_object_name = "report"
    template_name = "reports/update_report.html"
    success_url = reverse_lazy("reports")
    login_url = reverse_lazy("login")

    def form_valid(self, form):
        # get the instance to be saved in the DB
        report = form.save(commit=False)

        # status was changed
        if "status" in form.changed_data:
            status = form.cleaned_data["status"]
            report.status = status
            # update approvedBy and date_approve
            report.approvedBy = self.request.user.email or self.request.user.username
            report.date_approve = datetime.now()
        
        # accuracy was changed
        if "accuracy" in form.changed_data:
            accuracy = form.cleaned_data["accuracy"]
            report.accuracy = accuracy
        
        if "datapack" in form.changed_data:
            datapack_name = form.cleaned_data["datapack"]
            datapack_regex = re.compile(r'^[a-z]{3}-[A-Z]{3}-[A-Z]{3,}(\d\.\d+)?-(\d\.\d+)?\.\d+$')
            is_valid = bool(datapack_regex.search(datapack_name))
            if is_valid:
                report.datapack = datapack_name
                datapack_id = form.cleaned_data['datapack'].id
                datapack = get_object_or_404(DataPack, id=datapack_id)
                # Modify the datapack object as needed
                datapack.name = datapack_name
                datapack.save()

        # if 'file_report' in form.changed_data:
        #     file_report = form.cleaned_data['file_report']
        #     report.file_report = file_report
        
        if 'file_report' in form.changed_data and self.request.FILES:
            file_report = form.cleaned_data['file_report']
            report.file_report = file_report


        # update the report instance in the DB
        report.save()

        return super().form_valid(form)

class DeleteReportView(LoginRequiredMixin, DeleteView):
    model = Report
    success_url = reverse_lazy("reports")
    login_url = reverse_lazy("login")
    template_name = "reports/report_confirm_delete.html"

class DatapacksView(View):
    def get(self, request):
        """
        Displays the 100 latest datapacks and their reports
        """
        filter_form = DatapackFiltersForm()

        testing_types = TestingType.objects.all()
        datapacks = DataPack.objects.order_by("-id")[:100]

        datapacks_and_reports = []
        # datapacks_and_reports = [
        #    (
        #       datapack_1, {
        #       testing_type_1: [report_1, report_2, ...],
        #       testing_type_2: [report_1, report_2, ...],
        #       ...
        #       }
        #    ),
        #    (
        #       datapack_2, {
        #       testing_type_1: [report_1, report_2, ...],
        #       testing_type_2: [report_1, report_2, ...],
        #       ...
        #       }
        #    ),
        #    (
        #       datapack_3, {
        #       testing_type_1: [report_1, report_2, ...],
        #       testing_type_2: [report_1, report_2, ...],
        #       ...
        #       }
        #    ),
        #    ...
        # ]
        for datapack in datapacks:
            reports = {}
            # get all reports for this datapack
            datapack_reports = datapack.report_set.all()
            for testing_type in testing_types:
                report_w_testing_type_exists = datapack_reports.filter(testing_type=testing_type)
                if report_w_testing_type_exists:
                    reports[testing_type.name] = list(report_w_testing_type_exists)
                else:
                    reports[testing_type.name] = None
            datapacks_and_reports.append((datapack, reports))

        return render(
            request, "reports/dptracking/tracking.html", {
                "datapacks_and_reports": datapacks_and_reports,
                "filter_form": filter_form,
                "testing_types": testing_types
            }
        )

    def post(self, request):
        """
        Displays datapacks (filtered by the user's choices) and their reports.

        Datapacks of a certain topic (e.g. DTV datapacks) go through a specific set of tests.
        Therefore, when filtered by topic, only reports belonging to the topic's testing set are shown.

        e.g. user filters datapacks by topic
            - SIEPC topic is chosen
            - only MIX_accuracy_test_16k and ASR_functional_test reports are shown
                - this is because the SIEPC topic's testing set consists of only MIX_accuracy_test_16k and ASR_functional_test
                - please refer to the Topic model in models.py for more details
        """
        topic = None
        datapacks = DataPack.objects.all().order_by("-id")

        filter_form = DatapackFiltersForm(request.POST)
        if filter_form.is_valid():
            if "topic" in filter_form.changed_data:
                topic = filter_form.cleaned_data["topic"]
                datapacks = datapacks.filter(
                    topic=topic
                )
            if "language" in filter_form.changed_data:
                language = filter_form.cleaned_data["language"]
                datapacks = datapacks.filter(
                    language=language
                )

        if not topic:
            testing_types = TestingType.objects.all()
        else:
            testing_types = topic.tests_run.all()

        datapacks_and_reports = []
        for datapack in datapacks:
            reports = {}
            datapack_reports = datapack.report_set.all()
            for testing_type in testing_types:
                report_w_testing_type_exists = datapack_reports.filter(testing_type=testing_type)
                if report_w_testing_type_exists:
                    reports[testing_type.name] = list(report_w_testing_type_exists)
                else:
                    reports[testing_type.name] = None
            datapacks_and_reports.append((datapack, reports))

        return render(
            request, "reports/dptracking/tracking.html", {
                "datapacks_and_reports": datapacks_and_reports,
                "filter_form": filter_form,
                "testing_types": testing_types,
            }
        )

class UpdateDatapackView(LoginRequiredMixin, UpdateView):
    model = DataPack
    form_class = UpdateDatapackForm
    context_object_name = "datapack"
    template_name = "reports/update_datapack.html"
    success_url = reverse_lazy("dptracking")
    login_url = reverse_lazy("login")


def view_file(request, report_id):
    report = Report.objects.get(pk=report_id)
    file_path = report.file_report.path
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
    return response


def download_file(request, report_id):
    report = Report.objects.get(pk=report_id)
    file_path = report.file_report.path
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
    return response


# An endpoint to use for viewing and downloading files
class DownloadReportView(View):
    # Endpoint to allow users to view and download files within the application
    def get(self, request, report_id, download=False):
        report = Report.objects.get(pk=report_id)
        file_path = report.file_report.path
        response = FileResponse(open(file_path, 'rb'))
        if download:
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
        else:
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
        return response


# An endpoint to view the history of all reports belonging to the same datapack
class DatapackHistoryView(View):
    def get(self, request, datapack_name):
        template_name = "reports/dptracking/dphistory.html"
        all_reports = Report.objects.all()
        reports = []

        for report in all_reports:
            field_name = 'datapack'
            field_value = getattr(report, field_name)
            if str(field_value) == datapack_name.strip():
                reports.append(report)
        return render(
            request, template_name, {
                "dpname": datapack_name,
                "reports": reports,
            }
        )


def filter_stats(request):
  stats = []
  reports = []
  new_reports = []
  comparison = []
  # map choice label to actual statistic
  choice_to_stat_map = {
      "choice_0": "audio",
      "choice_1": "audiotx",
      "choice_2": "lag",
      "choice_3": "rec",
      "choice_4": "conf",
      "choice_5": "avg_latency",
      "choice_6": "95%_latency",
      "choice_7": "avg_cpl",
      "choice_8": "95%_cpl"
  }

  if request.method == 'POST':
    selected_choices = request.POST.getlist('choice')
    to_compare = request.POST.get('to_compare')

    for choice in selected_choices:
        stats.append(choice_to_stat_map[choice])

    reports = to_compare[2:-2].split(",")
    new_reports = []
    for report in reports:
        new_reports.append(report.replace("Report:", "").replace("<", "").replace(">", "").strip())
    
    # query the db for the reports with names in array new_reports
    report_objects = []
    for name in new_reports:
        #report = Report.objects.get(name=name)
        report = Report.objects.filter(name=name).first()
        report_objects.append(report)
    
    to_compare = [report for report in report_objects]

    comparison = compare_load_advanced(to_compare, False, False)

    # filter the desired stats from the comparison dict above
    selected_stats = set(stats)
    for dlm_key in comparison["stats"]:
        filtered_list = []
        for stat_dict in comparison["stats"][dlm_key]:
            filtered_dict = {}
            for stat_key in stat_dict:
                if stat_key in selected_stats:
                    filtered_dict[stat_key] = stat_dict[stat_key]
            filtered_list.append(filtered_dict)
        comparison["stats"][dlm_key] = filtered_list
        
    # convert all dictionaries back to strings
    for test_type in comparison["stats"]:
            stat_strs = []
            for stat in comparison["stats"][test_type]:
                stat_strs.append(dict_to_str(stat))
            comparison["stats"][test_type] = stat_strs
        
    for test_type in comparison["monitors"]:
        monitors_strs = []
        for monitors in comparison["monitors"][test_type]:
            single_monitor_str = ""
            for monitor in monitors:
                single_monitor_str += dict_to_str(monitor)
                single_monitor_str += "\n "
            monitors_strs.append(single_monitor_str)
        comparison["monitors"][test_type] = monitors_strs

    for test_type in comparison["errors"]:
        errs = []
        for errArr in comparison["errors"][test_type]:
            if len(errArr) == 0:
                errs.append("No Errors")
            else:
                errJoined = ""
                for errStr in errArr:
                    errJoined += f"{errStr}\n"
                errs.append(errJoined)
        comparison["errors"][test_type] = errs

  return render(request, 'reports/compare/compare_filtered.html', {
      "comparison_result": comparison,
      "to_compare": to_compare,
  })
