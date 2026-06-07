import boto3
from datetime import datetime, timezone, timedelta

s3 = boto3.client('s3')

BUCKET_NAME = "sailaja-cleanup-bucket"

def lambda_handler(event, context):

    threshold = datetime.now(timezone.utc) - timedelta(days=30)

    objects = s3.list_objects_v2(Bucket=BUCKET_NAME)

    deleted = []

    if 'Contents' in objects:

        for obj in objects['Contents']:

            if obj['LastModified'] < threshold:

                s3.delete_object(
                    Bucket=BUCKET_NAME,
                    Key=obj['Key']
                )

                deleted.append(obj['Key'])

    return {
        "Deleted Files": deleted
    }
