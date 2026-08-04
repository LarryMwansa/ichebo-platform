from django.shortcuts import render, redirect


def landing(request):
    if request.user.is_authenticated:
        return redirect('accounts:welcome')
    return render(request, 'join/landing.html')
