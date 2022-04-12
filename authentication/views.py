from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.message import EmailMessage
from multiprocessing import AuthenticationError
from click import get_current_context
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from login import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str#, force_text
from . tokens import generate_tokens
from django.utils.http import urlsafe_base64_decode
# Create your views here.
def home(request):
    return render(request,"authentication/index.html")

def signup(request):  
     if request.method == "POST":
         username = request.POST['username']
         fname = request.POST['fname']
         lname = request.POST['lname']
         email = request.POST['email']
         pass1 = request.POST['pass1']
         pass2 = request.POST['pass2']

         if User.objects.filter(username=username):
             messages.error(request, "Username already exist! Please try some other username.")
             return render(request, "authentication/signup.html")

         if User.objects.filter(email=email):
             messages.error(request, "Email already registered!")
             return render(request, "authentication/signup.html")

         if len(username)>10:
             messages.error(request, "Username must be under 10 characters!")
             return render(request, "authentication/signup.html")

         if pass1 != pass2:
             messages.error(request, "Password didn't match! Try again!!")
             #return redirect('home')
             return render(request, "authentication/signup.html")

         if not username.isalnum():
             messages.error(request, "Username must be Alpha-numeric")        
             return redirect('home')


         myuser = User.objects.create_user(username, email,pass1)
         myuser.first_name = fname
         myuser.last_name = lname

       #  myuser.is_active = False  #we will activate at as soom as the user will click on the sent link.
         myuser.save()
         messages.success(request, "Your account has been successfully created. ")
         #We have sent you a confirmation email, please confirm your email in order to activate your account.")



# Welcome Email
         subject = "Welcome to the page -Django Login!!"
         message = "Hello" + myuser.first_name +"!! \n "+ "Thank you for visiting our page\n We have also sent you a a confirmation email. Please confirm your email address."
         from_email = settings.EMAIL_HOST_USER
         to_list = [myuser.email]            # to whom we are seding the mail
         send_mail(subject, message, from_email, to_list, fail_silently=True)  # fail_silently, incase mail didnt reach, it wouldnt allow the code to crash


          #Email Address COnfiramtion Email

         current_site = get_current_context(request)
         email_subject = "Confirm your email!!"
         message2 = render_to_string('email_confirmation.html',{
              'name': myuser.first_name,
              'domain': current_site.domain,
              'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
              'token': generate_tokens.make_token(myuser),
 
          })
         email = EmailMessage (
              email_subject,
             message2,
              settings.EMAIL_HOST_USER,
              [myuser.email],
         )
         email.fail_silently = True
         email.send()          #

         return redirect('signin')


     return render(request, "authentication/signup.html")

def signin(request): 
        if request.method =='POST':
            username = request.POST['username']
            pass1 = request.POST['pass1']

            user= authenticate(username=username, password=pass1)
    
            if user is not None:
                login(request, user)
                fname = user.first_name
                return render (request, "authentication/index.html",{'fname': fname})

            else:
                messages.error(request, "Bad Credentials")
                return redirect('home')    
       
        return render(request, "authentication/signin.html") 

def signout(request): 
        logout(request)
        messages.success(request,"Logged out successfully")
        return redirect('home')

def activate(request, uidb64, token):
         try:
             uid = force_str(urlsafe_base64_decode(uidb64) )
             myuser =  User.objects.get(pk=uid)
         except(TypeError, ValueError, OverflowError, User.DoesNotExist):
             myuser = None

         if myuser is not None and generate_tokens.check_token(myuser, token):
             myuser.is_active = True
             myuser.save()   
             login(request, myuser)
             return redirect('home')   
         else:
              return render(request, 'activation_failed.html')     