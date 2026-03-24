from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages

# Create your views here.
def adminlogin(request):
    if request.method=="POST":
        username=request.POST.get("username")
        password=request.POST.get("password")
        data=authenticate(request,username=username,password=password)
        if data:
            if data.role =="ADMIN":
                login(request,data)
                return redirect("/adminhome/")
                
            else:
                messages.error(request,"invalid username or password")
        else:
            return redirect("selleregis")    
    return render(request,"admin-templates/adminlogin.html")


def adminhome(request):
    return render(request,"admin-templates/adminhome.html")