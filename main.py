import sys
import console
import json
import datetime
import time
import urllib.parse

import webbrowser
import boto3

import config


def support_datetime_default(o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()

    raise TypeError(repr(o) + " is not JSON serializable")

        
class AwsController():
    instance_id = config.instance_id
    aws_access_key_id = config.aws_access_key_id
    aws_secret_access_key = config.aws_secret_access_key
    region_name = config.region_name
    
    def __init__(self) -> None:
        self.instances = [self.instance_id]
        self.ec2 = boto3.client(
            'ec2',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )
    
    def start(self) -> None:
        self.ec2.start_instances(InstanceIds=self.instances)

    def stop(self) -> None:
        self.ec2.stop_instances(InstanceIds=self.instances)

    def fetch_instance_status(self) -> str:
        return \
            self.ec2.describe_instances(InstanceIds=self.instances)\
            ['Reservations'][0]\
            ['Instances'][0]\
            ['State']['Name']
 
    def fetch_instance_domain(self) -> str:
        return \
            self.ec2.describe_instances(InstanceIds=self.instances)\
            ['Reservations'][0]\
            ['Instances'][0]\
            ['NetworkInterfaces'][0]\
            ['Association']['PublicDnsName']

    def print_instance_data(self) -> str:
        print(json.dumps(
            self.ec2.describe_instances(InstanceIds=self.instances), 
            indent=2, 
            default=support_datetime_default
        ))

    def wait_until_running(self) -> bool:
        while self.fetch_instance_status() != 'running':
            print('waiting...')
            time.sleep(10)
        time.sleep(10)
        print('run!')
        return True


class BlinkController (object):
    BLINK_KEY = config.BLINK_KEY

    def connect_to(self, user_name, domain, ssh_key_name) -> None:
        print(
            'blinkshell://run?key=' + BlinkController.BLINK_KEY + 
            '&cmd=' + 
            urllib.parse.quote(
                'ssh -v -i "' + ssh_key_name + '" ' + 
                user_name + '@' + domain
            )
        )
        webbrowser.open(
            'blinkshell://run?key=' + BlinkController.BLINK_KEY + 
            '&cmd=' + 
            urllib.parse.quote(
                'ssh -v -i "' + ssh_key_name + '" ' + 
                user_name + '@' + domain
            )
        )


def main() -> None:
    aws_controller = AwsController()
    
#    aws_controller.print_instance_data()
    instance_status = aws_controller.fetch_instance_status()
    if instance_status == 'running':
        console.alert('now RUNNING','STOP?', 'yes', hide_cancel_button=False)
        aws_controller.stop()
    elif instance_status == 'stopped':
        console.alert('now STOPPED','RUN?', 'yes', hide_cancel_button=False)
        aws_controller.start()
        aws_controller.wait_until_running()

        blink_controller = BlinkController()
        blink_controller.connect_to(
            user_name=config.user_name,
            domain=aws_controller.fetch_instance_domain(),
            ssh_key_name=config.ssh_key_name
        )
    else:
        print('now stopping or pending. please exec later.')
    return


if __name__ == '__main__':
    main()
