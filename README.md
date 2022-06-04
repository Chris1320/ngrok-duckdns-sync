# Ngrok with DuckDNS

I wanted a way to combine the two and I think I have figured something out. Below is the image of how it works.

![duckdns -> redirection server -> ngrok -> main server](https://i.imgur.com/O1TDQ4u.png)

## Prequisites

- Python3
- Ability to use `sudo` or similar

## Installation

- DuckDNS
  - Get an account at [duckdns.org](https://duckdns.org/).
  - Register a domain name
  - Keep note of the token
- Ngrok
  - Get an accout at [ngrok.com](https://ngrok.com/signup)
  - Copy the authtoken
  - Download the binary from [ngrok.com](https://ngrok.com/download).  
  - Extract the binary and run `ngrok config authtoken <token>`
- Python3
  - Install `requests`