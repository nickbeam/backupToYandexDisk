# yaDisk Backup script

Script for backup files to Yandex Disk.

Script usage YaDisk. Is a Yandex.Disk REST API client library [YaDisk library](https://yadisk.readthedocs.io/en/latest/intro.html)

To get your `access_token`:

1. Register your app at [Yandex](https://oauth.yandex.ru/client/new)
    1. Be sure to check 'Yandex.Disk permits'
    2. Be sure to check 'Client for development' (it will set https://oauth.yandex.ru/verification_code?dev=True as `Callback URI`)
2. Get access token https://oauth.yandex.ru/authorize?response_type=token&client_id=YOUR_APP_ID
3. Get your access token from redirect url (right from the browser, it will be one of parameters)

## Installation

1. Download & Install Python 3.12 [Download Python](https://www.python.org/downloads/)
2. Install yadisk lib: `pip install yadisk`
3. Install yadisk lib: `pip install requests`

## Usage:

```python ./yaDisk_sync.py [-h] [-d DAYS] [-r] token source destination```

```commandline
positional arguments:
  token                 Access token
  source                Source path
  destination           Destination path

options:
  -h, --help            show this help message and exit
  -d DAYS, --days DAYS  Lifetime daily backups, days count (int) (Default 45)
  -r, --recursive       Recursive upload files
```
## Examples

#### Windows
`python .\yaDisk_sync.py "token" "C:\\Backup" "backup" -d 14`

#### Linux
`python ./yaDisk_sync.py "token" "/home/user/Backup" "backup" -d 14`