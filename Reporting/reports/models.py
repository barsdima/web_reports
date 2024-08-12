"""
Database models for Reporting project.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/db/models/
"""
from datetime import datetime
from django.db import models
from reports.utils.backend import get_upload_to
import re
import os
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

# Create your models here.

class TestingType(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self) -> str:
        return self.name

class Topic(models.Model):
    name = models.CharField(max_length=64)
    tests_run = models.ManyToManyField(TestingType)

    def __str__(self) -> str:
        return self.name


class Language(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self) -> str:
        return self.name




class DataPack(models.Model):
    name = models.CharField(max_length=64, null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.RESTRICT)
    topic = models.ForeignKey(Topic, on_delete=models.RESTRICT)
    version = models.CharField(max_length=64)
    STATUS_CHOICES = [
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("Not Released", "Not Released")
    ]
    status = models.TextField(
        choices=STATUS_CHOICES,
        default="In Progress"
    )

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def get_attributes_from_name(name: str):
        try:
            # DP name should be in form: language-topic-version
            # e.g. fra-FRA-GEN-4.1.3
            language, country, topic, version = name.split("-")
            topic = get_object_or_404(Topic, name=topic)
            language, _ = Language.objects.get_or_create(name=f"{language}-{country}")
            return (language, topic, version)
        except Exception as err:
            print(err)
            return (None, None, None)

    @staticmethod
    def is_valid_name(name: str) -> bool:
        datapack_regex = re.compile(r'^[a-z]{3}-[A-Z]{3}-[A-Z]{3,}(\d\.\d+)?-(\d\.\d+)?\.\d+$')
        return bool(datapack_regex.search(name))




class Environment(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self) -> str:
        return self.name


class Report(models.Model):
    name = models.CharField(max_length=200)
    datapack = models.ForeignKey(DataPack, on_delete=models.RESTRICT)
    testing_type = models.ForeignKey(TestingType, on_delete=models.RESTRICT)
    environment = models.ForeignKey(
        Environment, null=True, blank=True, on_delete=models.RESTRICT
    )
    tester = models.ForeignKey(get_user_model(), related_name="tester", on_delete=models.RESTRICT)
    STATUS_CHOICES = [
        ("Pending Approval", "Pending Approval"),
        ("Pass", "Pass"),
        ("Fail", "Fail")
    ]
    ACCURACY_CHOICES = [
        ("n/a", "n/a"),
        ("nadp", "nadp"),
        ("ndp", "ndp")
    ]
    status = models.TextField(
        choices=STATUS_CHOICES,
        default="Pending Approval"
    )
    date_submit = models.DateField(auto_now=True)
    date_approve = models.DateField(null=True, blank=True)
    file_report = models.FileField(upload_to=get_upload_to, null=True, blank=True)
    link_QAServer = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    jira = models.TextField(null=True, blank=True)
    accuracy = models.TextField(
        choices=ACCURACY_CHOICES,
        default="n/a"
    )
    approvedBy = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def create_new_report(object: dict, prefix: str = ""):
        try:
            # Check if object have all non-nullable fields
            name = object.get(f"{prefix}name", "")
            required_keys = [
                "name",
                "datapack",
                "testing_type",
            ]

            tester = object.get("tester")
            if not tester.is_authenticated:
                return {"report": name, "error": "Please login to create a new report"}

            for key in required_keys:
                if not object.get(f"{prefix}{key}"):
                    return {"report": name, "error": f"Missing value for {key}"}

            datapack_name = object.get(f"{prefix}datapack")
            if not DataPack.is_valid_name(datapack_name):
                return {"report": name, "error": "Datapack name not valid"}

            language, topic, version = DataPack.get_attributes_from_name(datapack_name)
            if not topic:
                _, _, topic_name, _ = datapack_name.split("-")
                return {"report": name, "error": f"{topic_name} is currently not supported. Please create a {topic_name} topic."}

            datapack, _ = DataPack.objects.get_or_create(
                name=datapack_name,
                defaults={"language": language, "topic": topic, "version": version},
            )
            testing_type = TestingType.objects.get(id=object.get(f"{prefix}testing_type"))

            environment = Environment.objects.get(id=object.get(f"{prefix}environment"))
            date_submit = object.get(f"{prefix}date_submit", datetime.today())
            link_QAServer = object.get(f"{prefix}link_QAServer", None)
            notes = object.get(f"{prefix}notes", None)
            jira = object.get(f"{prefix}jira", None)
            accuracy = object.get(f"{prefix}accuracy", None)
            file_report = object.get(f"{prefix}file_report", None)

            report = Report(
                name=name,
                datapack=datapack,
                testing_type=testing_type,
                environment=environment,
                tester=tester,
                date_submit=date_submit,
                link_QAServer=link_QAServer,
                file_report=file_report,
                notes=notes,
                jira=jira,
                accuracy=accuracy,
            )
            return report
        except Exception as err:
            return {"report": name, "error": f"{err}"}

    def extension(self):
        name, extension = os.path.splitext(self.file_report.name)
        return extension
