import os
import json
import hashlib
import shutil
import logging
import boto3
import time
from logging.handlers import TimedRotatingFileHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv
import pdb

load_dotenv()


class S3Syncer:
    def __init__(self, bucket_name, base_path):
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name
        self.base_path = base_path
        self.temp_dir = os.path.join(base_path, 's3syncer', 'temp')
        self.files_dir = os.path.join(base_path, 's3syncer', 'files')
        self.logs_dir = os.path.join(base_path, 's3syncer', 'logs')
        self.checksums = {}
        os.makedirs(self.logs_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = TimedRotatingFileHandler(os.path.join(self.logs_dir, 'sync.log'), when='midnight', backupCount=14)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def setup(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.files_dir, exist_ok=True)

    def download_and_verify(self, key, filename):
        for _ in range(3):  # try to download 3 times
            self.s3.download_file(self.bucket_name, key, filename)
            with open(filename, 'rb') as f:
                downloaded_file_checksum = hashlib.md5(f.read()).hexdigest()

            if downloaded_file_checksum == self.checksums.get(key):
                return True
            else:
                self.logger.error('Checksum mismatch for %s. Retrying...', key)
                time.sleep(5)

        self.logger.error('Failed to download %s after 3 attempts', key)
        return False

    def sync_directory(self):
        try:
            obj = self.s3.get_object(Bucket=self.bucket_name, Key='objects.json')
            data = json.loads(obj['Body'].read())
        except self.s3.exceptions.NoSuchKey:
            self.logger.error('objects.json does not exist in the bucket.')
            return
        except Exception as e:
            self.logger.error('An error occurred: %s', e)
            return

        self.checksums = {item['name']: item['checksum'] for item in data['files']}

        local_files = set()
        for root, dirs, files in os.walk(self.files_dir):
            for file in files:
                file_path = os.path.join(root, file)
                key = file_path[len(self.files_dir)+1:]
                local_files.add(key)

                if self.checksums.get(key):
                    with open(file_path, 'rb') as f:
                        file_checksum = hashlib.md5(f.read()).hexdigest()

                    if self.checksums[key] != file_checksum:
                        self.download_and_move(key, file_path)

        # Check for files not present locally
        for key in self.checksums:
            if key not in local_files and not key.endswith('/'):
                file_path = os.path.join(self.files_dir, key)
                self.download_and_move(key, file_path)

        event_handler = Watcher(self, self.checksums, self.logger, self.files_dir)
        observer = Observer()
        observer.schedule(event_handler, self.files_dir, recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()

        observer.join()

    def download_and_move(self, key, file_path):
        temp_filename = os.path.join(self.temp_dir, os.path.basename(file_path))
        if self.download_and_verify(key, temp_filename):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            shutil.move(temp_filename, file_path)
            self.logger.info('File downloaded successfully: %s', file_path)


class Watcher(FileSystemEventHandler):
    def __init__(self, syncer, checksums, logger, files_dir):
        self.syncer = syncer
        self.checksums = checksums
        self.logger = logger
        self.files_dir = files_dir

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        key = file_path[len(self.files_dir)+1:]

        if key in self.checksums:
            with open(file_path, 'rb') as f:
                file_checksum = hashlib.md5(f.read()).hexdigest()

            if self.checksums[key] != file_checksum:
                self.logger.info('File modified: %s. Starting download...', file_path)
                self.syncer.download_and_move(key, file_path)

    def on_deleted(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        key = file_path[len(self.files_dir)+1:]

        if key in self.checksums:
            if os.path.exists(file_path):
                self.logger.info('File moved, not deleted: %s', file_path)
                return
            self.logger.info('File deleted: %s. Starting download...', file_path)
            self.syncer.download_and_move(key, file_path)


if __name__ == '__main__':
    path = os.path.expanduser('~')
    env_dir = os.getenv('DIR', None)
    if env_dir:
        path = env_dir
    bucket_name = os.getenv('AWS_BUCKET', None)
    s3_syncer = S3Syncer(bucket_name, path)
    s3_syncer.setup()
    s3_syncer.sync_directory()
