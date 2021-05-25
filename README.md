#### Azure deployment

```
# url
https://filterapp.azurewebsites.net

# shell access
https://filterapp.scm.azurewebsites.net/webssh/host

# clone from main
git clone git@github.com:liwentn/filter.git
# run migrations manually using webssh to get database setup
# Change to the app folder
cd $APP_PATH
apt-get -y install python3-dev
apt-get -y install build-essential
# Activate the venv
source /antenv/bin/activate
# Install requirements
pip install -r requirements.txt
# set up the following environment variables
export DB_PASSWORD=
export DJANGO_SETTINGS_MODULE=filter.settings.local_pg
export EMAIL_HOST=smtp.gmail.com
export EMAIL_HOST_USER=filterapp2525@gmail.com
export EMAIL_HOST_PASSWORD=
# confirm migration status
python manage.py showmigrations
# run the following only if need to revert all migrations, and drop tables manually
python manage.py migrate --fake filterapp zero --settings=filter.settings.azure_pg

# Run database migrations
python manage.py migrate --settings=filter.settings.azure

# Create the super user (follow prompts)
python manage.py createsuperuser

# Azure CI will handle all subsequence deployment
# Add environment variables under Settings->Configuration 
# Refer to the above if there is a need to recreate the database

```

#### local deployment (macOS and Linux)
```
# initial setup
git clone git@github.com:liwentn/filter.git -b development
# cd to filter project before creating the virtual environment
virtualenv venv
# run deploy.sh
./deploy.sh
# if using gunicorn, replace python manage.py runserver with
gunicorn filter.wsgi
```

#### Azure deployment notes
- move log files out of the app direction. Otherwise there will be permission errors
- use whitenoise to manage static files. Collectstatic will be called by the build server
- manage.py can't be at sub folder. Has to be immediate under app folder otherwise Azure build server can't find it


- macOS Mojave or Catalina users may encounter issues when connecting Django to a MySQL database
```
ImportError: dlopen(..._mysql.cpython-38-darwin.so, 2): Library not loaded: @rpath/libmysqlclient.21.dylib
  Referenced from: .../site-packages/_mysql.cpython-38-darwin.so
  Reason: image not found
NameError: name '_mysql' is not defined
```
- the relative path (@rpath/libmysqlclient.21.dylib) seems to be causing the issue, changing the relative path to an absolute 
path will solve the problem
```
install_name_tool -change @rpath/libmysqlclient.21.dylib /usr/local/mysql/lib/libmysqlclient.21.dylib <path to _mysql.cpython-38-darwin.so>
# <path to _mysql.cpython-38-darwin.so> can be found in the error message under "Referenced from"
```


