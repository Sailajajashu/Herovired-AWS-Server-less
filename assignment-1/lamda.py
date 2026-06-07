import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    stop_instances = []
    start_instances = []

    response = ec2.describe_instances()

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:

            tags = instance.get('Tags', [])

            for tag in tags:

                if tag['Key'] == 'Action':

                    if tag['Value'] == 'Auto-Stop':
                        stop_instances.append(instance['InstanceId'])

                    elif tag['Value'] == 'Auto-Start':
                        start_instances.append(instance['InstanceId'])

    if stop_instances:
        ec2.stop_instances(InstanceIds=stop_instances)

    if start_instances:
        ec2.start_instances(InstanceIds=start_instances)

    return {
        "Stopped": stop_instances,
        "Started": start_instances
    }
