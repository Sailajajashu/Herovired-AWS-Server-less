import datetime
import os
import boto3
from botocore.exceptions import ClientError

# Initialize the EC2 client
ec2_client = boto3.client("ec2")

# Define Retention Period (30 Days)
RETENTION_DAYS = 30


def lambda_handler(event, context):
    # ------------------------------------------------------------
    # CONFIGURATION: Replace with your actual Volume ID
    # ------------------------------------------------------------
    volume_id = "vol-0dcf47bfaefe7a03f"  # <--- CHANGE THIS VALUE

    print(f"--- Starting Backup Process for Volume: {volume_id} ---")

    # ==========================================
    # 1. CREATE SNAPSHOT
    # ==========================================
    try:
        description = (
            f"Automated backup for {volume_id} created on "
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        snapshot = ec2_client.create_snapshot(
            VolumeId=volume_id,
            Description=description,
            TagSpecifications=[
                {
                    "ResourceType": "snapshot",
                    "Tags": [
                        {"Key": "CreatedBy", "Value": "AutomatedLambda"},
                        {"Key": "VolumeId", "Value": volume_id},
                    ],
                }
            ],
        )

        new_snapshot_id = snapshot["SnapshotId"]
        print(f"[SUCCESS] Created Snapshot ID: {new_snapshot_id}")

    except ClientError as e:
        print(f"[ERROR] Failed to create snapshot: {e.response['Error']['Message']}")
        return {"statusCode": 500, "body": "Snapshot creation failed."}

    # ==========================================
    # 2. CLEANUP OLD SNAPSHOTS (> 30 DAYS)
    # ==========================================
    print("\n--- Starting Cleanup Process for Snapshots Older Than 30 Days ---")

    # Calculate time boundary (localized to UTC since AWS uses UTC timestamps)
    time_limit = datetime.datetime.now(
        datetime.timezone.utc
    ) - datetime.timedelta(days=RETENTION_DAYS)

    try:
        # Filter to only scan snapshots created by this automated script for this specific volume
        response = ec2_client.describe_snapshots(
            Filters=[
                {"Name": "tag:CreatedBy", "Values": ["AutomatedLambda"]},
                {"Name": "tag:VolumeId", "Values": [volume_id]},
            ]
        )

        deleted_count = 0

        for snap in response["Snapshots"]:
            snap_id = snap["SnapshotId"]
            snap_start_time = snap["StartTime"]

            # Compare AWS snapshot timestamp with our 30-day time threshold
            if snap_start_time < time_limit:
                print(
                    f"Deleting expired Snapshot: {snap_id} (Created on: {snap_start_time.strftime('%Y-%m-%d')})"
                )
                ec2_client.delete_snapshot(SnapshotId=snap_id)
                deleted_count += 1

        print(f"[INFO] Cleanup complete. Deleted {deleted_count} old snapshots.")

    except ClientError as e:
        print(f"[ERROR] Failed during cleanup: {e.response['Error']['Message']}")

    return {
        "statusCode": 200,
        "body": f"Process completed. New Snapshot: {new_snapshot_id}. Old snapshots cleaned up.",
    }
