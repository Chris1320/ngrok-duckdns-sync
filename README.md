# Ngrok with DuckDNS

I wanted a way to combine the two and I think I have figured something out. Below is the image of how it works.

![duckdns -> redirection server -> ngrok -> main server](https://i.imgur.com/O1TDQ4u.png)

## Prequisites

- Python 3

## Installation

- 1. Getting your DuckDNS domain name
    1. Register for a free [DuckDNS](https://duckdns.org/) account.
    2. Register a domain name.
    3. Replace the `duckdns_domain` and `duckdns_token` in `redirector/config.conf` with your own DuckDNS domain name and token, respectively.
- 2. Setting up ngrok
    1. Register for a free [ngrok](https://ngrok.com/signup) account.
    2. Copy your [auth token](https://dashboard.ngrok.com/get-started/your-authtoken) and replace the value of `ngrok_auth_token` with your auth token.
- 3. Setting up your redirection server (Using [PythonAnywhere](https://pythonanywhere.com/))
    1. Register for a free [PythonAnywhere](https://pythonanywhere.com/) account.
    2. Add a new web app.
        - Choose **Flask** as the Python Web Framework.
        - Select the latest supported Python version (as of this writing, it is **Python 3.10**)
        - Set the path of the Flask project. (I will set it to `/home/<username>/redirector/redirector.py`)
    3. Create a new directory `/home/<username>/redirector/`.
    4. Upload the contents of `redirector/` in your machine into the new web app's directory.
    5. Edit the WSGI Python file. (Usually located in `/var/www/<username>_pythonanywhere_com_wsgi.py`)
        - Before the line with `from redirector import app as application  # noqa`, add the following code:

            ```python
            from redirector import main
            main("<PATH_TO_CONFIG_FILE>")
            ```

    6. Save the file and restart the server.
    7. Open the server logs (located in `/var/log/<username>.pythonanywhere.com.server.log`) and get your redirector API key. Look for something like this:

        ```
        [i] New API key has been set. You'll only see this once:
        6f024c51ca5d0b6568919e134353aaf1398ff090c92f6173f5ce0315fa266b93
        ```

- 4. Setting up the tunnel client.
    1. Fill up the `config.conf` file of the `tunnel.py` script.
        - **server_port**: The port of the local server you want to expose.
        - **protocol**: The protocol to pass to ngrok (i.e., `http` or `tcp`)
        - **update_url**: The URL of the redirection server.
        - **update_port**: The port of the redirection server.
        - **update_url_https**: Set this to true to use *https* instead of *http*.
        - **api_key**: The API key you saw from the redirection server's server logs from *step 3.7*.
        - **duckdns_domain**: The name of your DuckDNS subdomain.
        - **duckdns_token**: The token of your DuckDNS account.
        - **tunnel_name**: The name of your ngrok tunnel. (What you will see in your ngrok dashboard)
        - **ngrok_auth_token**: Your ngrok authentication token.
- 5. It should be ready to use now! When you visit `<domain>.duckdns.org`, you will be redirected to your ngrok instance.

## Troubleshooting

### I am getting a `403 Forbidden` error!

If you are getting a `403 Forbidden` error, make sure that you have set the correct API key in the `config.conf` file.

### I am getting a `502 Bad Gateway` error!

If you are getting a `502 Bad Gateway` error, make sure that you have set the correct path of the Flask project in the PythonAnywhere web app settings.

### I am getting a `503 Service Unavailable` error!

If you are getting a `503 Service Unavailable` error, make sure that `tunnel.py` is running and has successfully updated the redirection server for the ngrok instance address.

### I cannot connect to the redirection server!

If you use **[PythonAnywhere](https://pythonanywhere.com/)** as your redirection server, try to change the port of the web app to `80`. If you are using a **different redirection server**, make sure that the redirection server is running and that you have set the correct port in the `config.conf` file. Otherwise, check the output of `tunnel.py` for any errors.
