from django.http import HttpResponse
from django.conf import settings
import traceback


class ErrorHandlerMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    # TODO: Add relative path to this file to the MIDDLEWARE section in the settings.py
    def process_exception(self, request, exception):
        if not settings.DEBUG:
            if exception:
                message = "**{url}**\n\n{error}\n\n````{tb}````".format(
                    url=request.build_absolute_uri(),
                    error=repr(exception),
                    tb=traceback.format_exc()
                )
                # TODO: implement feature here to to send error messages Teams channel
                # https://stackoverflow.com/questions/59371631/send-automated-messages-to-microsoft-teams-using-python
                # OR
                # i.e. requests.post(<teams channel>, data=message)
                
            return HttpResponse("Error processing the request.", status=500)