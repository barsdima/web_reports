from django import forms
from django.forms import ModelForm, TextInput, FileInput, Textarea, formset_factory, ClearableFileInput

from reports.models import (
    Report,
    Environment,
    TestingType,
    Topic,
    Language,
    DataPack,
)
from django.contrib.auth import get_user_model

class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    email = forms.EmailField(required=False, label="Your e-mail address")
    message = forms.CharField(widget=forms.Textarea)
    choiceField = forms.ChoiceField()

    def clean_message(self):
        message = self.cleaned_data["message"]
        num_words = len(message.split())
        if num_words < 4:
            raise forms.ValidationError("Not enough words!")
        return message




class TestingTypeForm(forms.Form):
    testing_types = forms.ModelChoiceField(
        queryset=TestingType.objects.all().exclude(name__exact="").order_by("name"),
        empty_label="Select test type...",
    )


class ReportFiltersForm(forms.Form):
    datapack = forms.ModelChoiceField(
        queryset=(
            DataPack.objects.filter(name__isnull=False)
            .exclude(name__exact="")
            .order_by("name")
        ),
        empty_label="DataPack",
        required=False,
    )
    language = forms.ModelChoiceField(
        queryset=(
            Language.objects.filter(name__isnull=False)
            .exclude(name__exact="")
            .order_by("name")
        ),
        empty_label="Language",
        required=False,
    )
    topic = forms.ModelChoiceField(
        queryset=(
            Topic.objects.filter(name__isnull=False)
            .exclude(name__exact="")
            .order_by("name")
        ),
        empty_label="Topic",
        required=False,
    )
    test_type = forms.ModelChoiceField(
        queryset=(
            TestingType.objects.filter(name__isnull=False)
            .exclude(name__exact="")
            .order_by("name")
        ),
        empty_label="Testing type",
        required=False,
    )
    environment = forms.ModelChoiceField(
        queryset=(
            Environment.objects.filter(name__isnull=False)
            .exclude(name__exact="")
            .order_by("name")
        ),
        empty_label="Environment",
        required=False,
    )
    tester = forms.ModelChoiceField(
        queryset=(
            get_user_model().objects.all()
        ),
        empty_label="Tester",
        required=False,
    )


class UploadForm(forms.Form):
    title = forms.CharField(max_length=50, required=False)
    file = forms.FileField()


class DocumentForm(forms.Form):
    docfile = forms.FileField(label="Select a file", help_text="max. 42 megabytes")


class SubmitreportForm(ModelForm):
    class Meta:
        model = Report
        fields = [
            "file_report",
            "name",
            "accuracy",
            "datapack",
            "testing_type",
            "environment",
            "link_QAServer",
            "jira",
            "notes",
        ]
        widgets = {
            "datapack": TextInput(),
            "link_QAServer": TextInput(),
            "jira": TextInput(),
            "notes": Textarea(),
        }


SubmitreportFormSet = formset_factory(SubmitreportForm, extra=0)

class ForeignKeyTextInput(TextInput):
    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model

    def get_context(self, name, value, attrs):
        # Get the related object for the foreign key
        obj = self.model.objects.get(pk=value) if value else None

        # Set the value of the widget to the name of the related object
        if obj:
            attrs['value'] = obj.name

        return super().get_context(name, value, attrs)

class UpdateReportForm(ModelForm, forms.Form):
    testing_type = forms.ModelChoiceField(queryset=TestingType.objects.all())
    environment = forms.ModelChoiceField(queryset=Environment.objects.all())

    class Meta:
        model = Report
        fields = [
            "name",
            "testing_type",
            "environment",
            "status",
            "notes",
            "link_QAServer",
            "jira",
            "accuracy",
            "file_report"
        ]
        widgets = {
            "notes": Textarea(attrs={'style': 'width: 700px; height: 100px'}),
            "link_QAServer": TextInput(attrs={'style': 'width: 700px'}),
            "jira": TextInput(attrs={'style': 'width: 700px'}),
            "name": TextInput(attrs={'style': 'width: 700px'}),
            "file_report": FileInput(),
        }

class DatapackFiltersForm(forms.Form):
    topic = forms.ModelChoiceField(
        queryset=(
            Topic.objects.filter(name__isnull=False)
            .exclude(name__exact="")
            .order_by("name")
        ),
        empty_label="Topic",
        required=False,
    )
    language = forms.ModelChoiceField(
        queryset=(
            Language.objects.filter(name__isnull=False)
            .exclude(name__exact="")
            .order_by("name")
        ),
        empty_label="Language",
        required=False,
    )

class UpdateDatapackForm(ModelForm):
    class Meta:
        model = DataPack
        fields = [
            "status",
        ]
