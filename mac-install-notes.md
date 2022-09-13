## Notes on running this on a mac

1. Locally the app runs on ssl, so you will need to generate a local certificate and add it to a `certs/` folder in the root directory. It is used in the `.flaskenv` file.
    ```
    openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
    ```
1. You need to install a few things in the os.
    ```
    brew install mupdf swig freetype redis postgresql
    ```
1. Some macs have issues with multithreading and cause python to crash. Lurnby uses redis to run background tasks which might cause python to crash. You need to set an environment variable to fix this.
    ```
    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
    ```
1. You will need 3 terminal tabs for lurnby to run
    ```
    1. Flask app - flask run
    2. Redis - redis-server
    3. Redis Queue - rq worker lurnby-tasks
    ```