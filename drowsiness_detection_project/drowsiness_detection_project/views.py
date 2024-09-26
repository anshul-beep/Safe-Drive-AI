from django.http import JsonResponse
from django.shortcuts import render

def about_view(request, *args, **kwargs):
    return render(request,'accounts\login.html',{})