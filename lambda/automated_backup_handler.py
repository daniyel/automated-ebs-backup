import os
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

def delete_snapshot(snapshot_id, region):
    print(f'Deleting snapshot {snapshot_id}.')
    try:
        ec2resource = boto3.resource('ec2', region_name=region)
        snapshot = ec2resource.Snapshot(snapshot_id)
        snapshot.delete()
    except ClientError as error:
        print(f'Caught exception: {error}.')

    return

def lambda_handler(event, context):
    region = os.environ['REGION']
    account_id = os.environ['ACCOUNT_ID']
    vol_name_prefixes = os.environ['VOL_NAME_PREFIXES']
    retention_in_days = int(os.environ['RETENTION_IN_DAYS'])
    ec2 = boto3.client('ec2', region_name=region)
    now = datetime.now()
    filters = []
    prefixes = vol_name_prefixes.split()

    for prefix in prefixes:
        if not prefix.endswith('*'):
            prefix = f'{prefix}*'
        filters.append({'Name': 'tag:Name', 'Values': [f'{prefix}']})

    # Get all or specific volumes in region
    volumes = ec2.describe_volumes(Filters=filters)

    for volume in volumes['Volumes']:
        print(f'Backing up {volume["VolumeId"]} in {volume["AvailabilityZone"]}.')

        # Create snapshot
        snapshot = ec2.create_snapshot(VolumeId=volume['VolumeId'], Description='Created by Lambda backup function')

        # Get snapshot resource
        ec2resource = boto3.resource('ec2', region_name=region)
        snapshot_id = ec2resource.Snapshot(snapshot['SnapshotId'])

        volume_tag = f'{volume["VolumeId"]}'

        # Find name tag for volume if it exists
        if 'Tags' in volume:
            for tags in volume['Tags']:
                if tags['Key'] == 'Name':
                    volume_tag = tags['Value']

        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        volume_name = f'{volume_tag}-{timestamp}'

        # Add volume name to snapshot for easier identification
        print(f'Tagging {volume["VolumeId"]} with {volume_name}.')
        snapshot_id.create_tags(Tags=[{'Key': 'Name', 'Value': volume_name}])

    snapshots = ec2.describe_snapshots(Filters=filters, OwnerIds=[account_id])

    for snapshot in snapshots['Snapshots']:
        print(f'Checking snapshot {snapshot["SnapshotId"]} which was created on {snapshot["StartTime"]}.')

        # Remove timezone info from snapshot in order for comparison to work below
        snapshot_time = snapshot['StartTime'].replace(tzinfo=None)

        # Subtract snapshot time from now returns a timedelta
        # Check if the timedelta is greater than retention days
        if (now - snapshot_time) > timedelta(days=retention_in_days):
            print(f'Snapshot is older than configured retention of {retention_in_days} days.')
            delete_snapshot(snapshot['SnapshotId'], reg)
        else:
            print(f'Snapshot is newer than configured retention of {retention_in_days}. Keeping snapshot.')
