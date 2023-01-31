# 6obcy-python-cli
A 6obcy command-line client built in Python that is simple and easy to use.
## Features

- **No web browser needed at all (uses websockets, doesn't depend on selenium)**
- Automatically connect and solve captcha (using 2Captcha API, more below)
- Automatically ask for stranger's gender
- Disconnect automatically when found "M"
- Ring a bell when found "K"
- Log all conversations into files
- Save all solved captchas (in case you want to have some fun trying to crack them using machine learning)
- Properly integrates with 2Captcha API and reports both well and wrongly resolved captchas

## Installation
Python3 required to run.
Install the dependencies from `requirements.txt`:
```
pip3 install -r requirements.txt
```
or
```
pip3 install 2captcha-python beepy websocket-client
```

## Usage
```
python3 main.py <YOUR_API_KEY>
```
Just wait for beep and type :)
If you want to close the conversation, type `:q`

## Captcha solving API
This project uses 2Captcha as the captcha solving api.
Therefore, you need to specify an API key.
**NOTE: You don't actually have to pay for it with money. You can just register as a worker and solve some captchas.**

## TODO

 - (fix) The "km" request goes to the end of the last conversation log
 - Better management of typing state (should use a non-blocking input)
