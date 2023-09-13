import json
import boto3
import hashlib


def compute_md5(body):
    hash_md5 = hashlib.md5()
    for chunk in iter(lambda: body.read(4096), b""):
        hash_md5.update(chunk)
    return hash_md5.hexdigest()


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Skip if the uploaded file is objects.json
    if key == 'objects.json':
        return {
            'statusCode': 200,
            'body': json.dumps('objects.json upload detected. Skipping MD5 calculation.')
        }

    # Get the uploaded file
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj['Body']

    # Compute MD5 checksum of the file
    md5_checksum = compute_md5(body)

    # Get the existing objects.json content or create a new one if it does not exist
    try:
        objects_json = s3.get_object(Bucket=bucket, Key='objects.json')
        objects = json.loads(objects_json['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        objects = {'files': []}

    # Append the new object and its MD5 checksum
    new_object = {'name': key, 'checksum': md5_checksum}
    objects['files'].append(new_object)

    # Write the updated objects.json back to S3
    s3.put_object(Bucket=bucket, Key='objects.json', Body=json.dumps(objects))

    return {
        'statusCode': 200,
        'body': json.dumps('MD5 checksum appended to objects.json')
    }
