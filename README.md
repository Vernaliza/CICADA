```text
   ██████╗ ██╗ ██████╗ █████╗ ██████╗  █████╗
  ██╔════╝ ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗
  ██║      ██║██║     ███████║██║  ██║███████║
  ██║      ██║██║     ██╔══██║██║  ██║██╔══██║
  ╚██████╗ ██║╚██████╗██║  ██║██████╔╝██║  ██║
   ╚═════╝ ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝  v0.1.0
```

What is CICADA？

CICADA is a Command-line Integration for Continuous Automated Django Administration  
<br>
It helps developers quickly set up a production-ready Django environment including:

　　　　system dependencies
    
　　　　Python virtual environment
    
　　　　Gunicorn
    
　　　　Nginx configuration
    
　　　　systemd service

　　　　automatic project setup
  
<br>
The project is still under construction...
<br>
<br>
<br>
If I want to use CICADA, what should I do first?

　　　　you should have a Linux server for running your project and another server for save database!

　　　　Then you need to edit your settings.py of your Django project. Check following codes!


    DEBUG = False
    ALLOWED_HOSTS = ['your_server_ip', 'your_domain', 'localhost', '127.0.0.1']
    
    CSRF_TRUSTED_ORIGINS = [
        "http://your_domain",
        "https://your_domain",
    ]
    
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "your_database_name",
            "USER": "database_username",
            "PASSWORD": "database_password",
            "HOST": "your_RDS_IP_address_or_AWS_endpoint",  # e.g. xxx.rds.amazonaws.com
            "PORT": "3306",
        }
    }
    
    STATIC_URL = "/static/"
    STATIC_ROOT = "/var/www/<project_name>/static"
    
    MEDIA_URL = "/media/"
    MEDIA_ROOT = "/var/www/<project_name>/media"

　　　　After that, run CICADA in your Linux server.

　　　　In version, you have to apt python first.

    sudo apt update
    sudo apt install python3 python3-pip -y

　　　　You need to enter the holder where CICADA is.

    cd <the place where CICADA is>

　　　　Now you can run CICADA!

    sudo python cicada_v0.1.0.py

　　　　or

    chmod +x cicada_v0.1.0.py #this line only needs to be run on the first attempt
    ./cicada_v0.1.0.py

　　　　Now finish! Have fun!