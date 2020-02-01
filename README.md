# Robot Travel
Welcome to Robot Travel - your travel optimizer assistant!

This is the supporting API for the main application and must not be confused with the client module.

Check out the internal documentation to see what does each endpoint do.

<hr>

## Google App Engine Requirements
This server was initially built to be deployed using Google App Engine.
As a result, there are several environment variables that were added to a <code>app.yaml</code> file.
Here are some that you might need to add while deploying this.
Also, please note that several are required for adding Google Cloud SQL support.
You may remove them if you are planning to use a different database.

<pre>
PROJECT_ID: enter_project_id
DATA_BACKEND: 'cloudsql'
CLOUDSQL_USER: enter_username
CLOUDSQL_PASSWORD: enter_password
CLOUDSQL_DATABASE: enter_database_name
CLOUDSQL_CONNECTION_NAME: enter_connection_name
</pre>
<hr>

## Contact Info
In case of any queries, please feel free to contact Rachit Bhargava (developer) at rachitbhargava99@gmail.com.

## Third-Party Use
This application cannot be used for any unauthorized uses.
If you are interested in using the application for any purposes, please contact the developer for permissions.