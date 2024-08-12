import json

from django.shortcuts import render


def date_handler(obj):
    return obj.isoformat() if hasattr(obj, "isoformat") else obj


def get_reports_json(reports) -> str:
    list = []
    for report in reports:
        approvedate = str(report.date_approve)
        if approvedate == "None":
            approvedate = ""

        try:
            testing_type = report.testing_type.name
        except:
            testing_type = ""

        raw = {
            "reportid": report.id,
            "ReportName": report.name,
            "Environment": report.environment.name,
            "Topic": report.datapack.topic.name,
            "Language": report.datapack.language.name,
            "Tester": report.tester.name,
            "Status": report.status,
            "SubmittedDate": str(report.date_submit),
            "ApprovedDate": approvedate,
            "Path": report.link_QAServer,
            "Notes": report.notes,
            "JIRA": report.jira,
            "Accuracy": report.accuracy,
            "Datapack": report.datapack.name,
            "ApprovedBy": report.approvedBy,
            "TestingType": testing_type,
            "Parameters": report.parameters,
        }

        list.append(raw)
    return json.dumps(list, default=date_handler)
