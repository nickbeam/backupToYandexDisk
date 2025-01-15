import posixpath
import os
import yadisk
import datetime
import argparse
import logging
from pathlib import Path


# Arguments parser configuration
parser = argparse.ArgumentParser()
parser.add_argument("token", type=str, help="Access token")
parser.add_argument("source", type=str, help="Source path")
parser.add_argument("destination", type=str, help="Destination path")
parser.add_argument("-r", "--recursive", help="Recursive upload files", action="store_true")
parser.add_argument("-d", "--days", type=int, help="Lifetime daily backups, days count (int) (Default 45)")
args = parser.parse_args()

# Create log directory if not exist
Path("logs").mkdir(parents=True, exist_ok=True)

# Logging configuration
logger = logging.getLogger('backup')
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler = logging.FileHandler(f"{Path().resolve()}{os.path.sep}logs{os.path.sep}backup-{datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')}.log", mode='a')
stream_handler = logging.StreamHandler()
file_handler.setFormatter(log_formatter)
stream_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# YD client configuration
client = yadisk.Client(token=args.token)

# Define the source and destination constants
SOURCE_PATH = args.source
DESTINATION_PATH = args.destination

# Subdirectory names configuration
DAILY_BACKUP_PATH = DESTINATION_PATH + '/Daily'
MONTHLY_BACKUP_PATH = DESTINATION_PATH + '/Monthly'
YEARLY_BACKUP_PATH = DESTINATION_PATH + '/Yearly'

# File lifetime configuration
YEARLY_BACKUP_DAYS_OF_LIFE = 1825
MONTHLY_BACKUP_DAYS_OF_LIFE = 365
DAILY_BACKUP_DAYS_OF_LIFE = 45
if not (args.days is None):
    DAILY_BACKUP_DAYS_OF_LIFE = args.days


# Workaround for slow loading of archives to Yandex Disk due to online antivirus scanning
def rename_arch_extensions(file_path: str):
    if file_path.find('.zip') != -1:
        file_path = file_path.replace('.zip', '.zi_p')
    elif file_path.find('.7z') != -1:
        file_path = file_path.replace('7z', '.7_z')
    elif file_path.find('.rar') != -1:
        file_path = file_path.replace('.rar', '.ra_r')
    return file_path


def upload_files(upload_from_dir: str, upload_to_dir: str):
    logger.info(f"===Search files to upload at {upload_from_dir}")
    if os.path.exists(upload_from_dir) is False:
        logger.error(upload_from_dir + "is not exist")
        exit(1)

    for file in os.listdir(upload_from_dir):
        if os.path.isfile(os.path.join(upload_from_dir, file)):
            p = upload_from_dir.split(upload_from_dir)[1].strip(os.path.sep)
            dir_path = posixpath.join(upload_to_dir, p).replace("\\", "/")

            out_path = posixpath.join(dir_path, file)
            p_sys = p.replace("/", os.path.sep)
            in_path = os.path.join(upload_from_dir, p_sys, file)

            out_path = rename_arch_extensions(out_path)
            if not file_exists(out_path):
                try:
                    logger.info(f"Uploading {in_path} -> {out_path}")
                    client.upload(in_path, out_path, timeout=(15, 250))
                except yadisk.exceptions.PathExistsError:
                    logger.error(f"{out_path} already exists")
                    pass


def recursive_upload_files(upload_from_dir: str, upload_to_dir: str):
    logger.info(f"===Search files to recursive upload at {upload_from_dir}")
    for root, dirs, files in os.walk(upload_from_dir):
        p = root.split(upload_from_dir)[1].strip(os.path.sep)
        dir_path = posixpath.join(upload_to_dir, p).replace("\\", "/")

        try:
            print(f"Creating directory {dir_path}")
            client.mkdir(dir_path)
        except yadisk.exceptions.PathExistsError:
            print(f"{dir_path} already exists")
            pass

        for file in files:
            out_path = posixpath.join(dir_path, file)
            p_sys = p.replace("/", os.path.sep)
            in_path = os.path.join(upload_from_dir, p_sys, file)

            out_path = rename_arch_extensions(out_path)
            if not file_exists(out_path):
                try:
                    print(f"Uploading {in_path} -> {out_path}")
                    client.upload(in_path, out_path, timeout=(15, 250))
                except yadisk.exceptions.PathExistsError:
                    print(f"{out_path} already exists")
                    pass


def delete(del_from_dir: str, days_of_life: int):
    logger.info(f"Search files to delete at {del_from_dir} older than {days_of_life} day(s)")
    for file in client.listdir("/" + del_from_dir):
        if file.is_file():
            to_date = datetime.date.today() - datetime.timedelta(days=days_of_life)
            if file.created.date() < to_date:
                logger.info(f"Deleting file {file.path}")
                if file_exists(file.path):
                    try:
                        client.remove(file.path, permanently=True)
                    except yadisk.exceptions.PathNotFoundError:
                        logger.error(f"{file.path} not exists")
                        pass


def sort_files(copy_from_dir: str):
    logger.info(f"=== Search files to sort at {copy_from_dir}")
    for file in client.listdir("/" + copy_from_dir):
        if file.is_file():
            past_year = datetime.date.today() - datetime.timedelta(days=365)
            if file.created.date().day == 1 and file.created.date() > past_year:
                new_path = MONTHLY_BACKUP_PATH + "/" + file.name
                logger.info(f"Copying file {file.path} to {new_path}")
                if not file_exists(new_path):
                    try:
                        client.copy(file.path, new_path)
                    except yadisk.exceptions.PathExistsError:
                        logger.error(f"{new_path} already exists")
                        pass
            if file.created.date().day == 1 and file.created.date().month == 12:
                new_path = YEARLY_BACKUP_PATH + "/" + file.name
                logger.info(f"Copying file {file.path} to {new_path}")
                if not file_exists(new_path):
                    try:
                        client.copy(file.path, new_path)
                    except yadisk.exceptions.PathExistsError:
                        logger.error(f"{new_path} already exists")
                        pass


def file_exists(file_path: str) -> bool:
    if client.exists(file_path):
        logger.info(f"{file_path} already exists")
        return True
    else:
        logger.info(f"{file_path} not exists")
        return False


def mkdir(dir_name: str):
    logger.info(f"Creating directory {dir_name}")
    if not file_exists(dir_name):
        try:
            client.mkdir(dir_name)
        except yadisk.exceptions.PathExistsError:
            logger.error(f"{dir_name} already exists")


def check_dir_tree(remote_root_dir: str):
    logger.info(f"=== Check the directory tree")
    mkdir(remote_root_dir)
    mkdir(YEARLY_BACKUP_PATH)
    mkdir(MONTHLY_BACKUP_PATH)
    mkdir(DAILY_BACKUP_PATH)


def cleanup_remote_dirs(remote_root_dir: str):
    logger.info(f"=== Cleanup directories")
    delete(YEARLY_BACKUP_PATH, YEARLY_BACKUP_DAYS_OF_LIFE)
    delete(MONTHLY_BACKUP_PATH, MONTHLY_BACKUP_DAYS_OF_LIFE)
    delete(DAILY_BACKUP_PATH, DAILY_BACKUP_DAYS_OF_LIFE)


logger.info("*** Start backup " + datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S'))
check_dir_tree(DESTINATION_PATH)
if args.recursive:
    recursive_upload_files(SOURCE_PATH, DAILY_BACKUP_PATH)
else:
    upload_files(SOURCE_PATH, DAILY_BACKUP_PATH)
sort_files(DAILY_BACKUP_PATH)
cleanup_remote_dirs(DESTINATION_PATH)
logger.info("*** End backup " + datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S'))
