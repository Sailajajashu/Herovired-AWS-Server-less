import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    unencrypted_buckets = []
    encrypted_buckets = []
    
    try:
        response = s3_client.list_buckets()
        buckets = response.get('Buckets', [])
        
        print(f"Found {len(buckets)} total buckets to analyze.\n")
        
        for bucket in buckets:
            # Safe extraction: handles if bucket is a dict or unexpectedly a string
            if isinstance(bucket, dict):
                bucket_name = bucket.get('test-hero1')
            else:
                bucket_name = bucket  # Fallback if it's already a string string
                
            if not bucket_name:
                continue

            try:
                s3_client.get_bucket_encryption(Bucket=bucket_name)
                encrypted_buckets.append(bucket_name)
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                    unencrypted_buckets.append(bucket_name)
                else:
                    print(f"Could not check bucket {bucket_name} due to error: {e}")
        
        print("--- AUDIT RESULTS ---")
        if unencrypted_buckets:
            print(f"⚠️ WARNING: Found {len(unencrypted_buckets)} UNENCRYPTED bucket(s):")
            for b in unencrypted_buckets:
                print(f"  - {b}")
        else:
            print("✅ Clean bill of health! No unencrypted buckets found.")
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'unencrypted_buckets_count': len(unencrypted_buckets),
                'unencrypted_buckets_list': unencrypted_buckets
            })
        }

    except Exception as e:
        print(f"Execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Internal script error occurred: {str(e)}")
        }
