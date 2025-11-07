from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .models import Members

# Create your views here.
def display_members(request):
    return HttpResponse("Hello Place of Refuge Church!")

'''
def display_members(request):
    churchmembers = Members.objects.all().values()
    template = loader.get_template('display_members.html')
    context = {
        'churchmembers': churchmembers
    }

    return HttpResponse(template.render(context, request))
'''