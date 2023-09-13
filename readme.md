# S3Syncer

## Description

S3Syncer is a tool to synchronize files between an Amazon S3 bucket and a local directory. It checks the MD5 checksums of the files in the local directory against the checksums stored in a JSON file in the S3 bucket and downloads any missing or modified files. It also watches the local directory for any changes and downloads the corresponding files from the S3 bucket if necessary.

## Requirements

- Python 3
- Boto3
- Watchdog

## Installation

1. Clone the repository.
2. Navigate to the project directory.
3. Edit the `s3_syncer.conf` file and update the paths accordingly.
4. Run the `setup.sh` script to create a virtual environment, install the required packages and copy the `s3_syncer.conf` file to the supervisor config directory.
5. Update the `.env.example` file with your S3 bucket name and AWS credentials and rename it to `.env`.
6. The `objects.json` file are created by the lambda function `s3FileProcessor.py` in the `lambda` directory. It needs to be deployed to AWS Lambda and triggered by an S3 event.

## Usage

Start the service installed by the `setup.sh` script with the following command:

```bash
sudo supervisorctl start s3_syncer
```

## License

This project is licensed under the MIT License.

---
Created by [Alexander Fuchs](https://github.com/Alexander-Fuchs)