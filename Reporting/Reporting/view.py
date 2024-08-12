from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout

def home(request):
    return render(request, "reports/home.html")

def login_view(request):
    if request.method == "GET":
        return render(request, "reports/login.html")

    if request.method == "POST":
        redirect_to = request.GET.get("next", "/")

        if request.user.is_authenticated:
            return HttpResponseRedirect(redirect_to)

        else:
            # Do something for anonymous users.
            username = request.POST.get("username", "")
            password = request.POST.get("password", "")
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect(redirect_to)

                else:
                    # Return a 'disabled account' error message
                    return HttpResponse("Account disabled.")

            else:
                # Return an 'invalid login' error message.
                return render(request, 'reports/login.html')

def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")
