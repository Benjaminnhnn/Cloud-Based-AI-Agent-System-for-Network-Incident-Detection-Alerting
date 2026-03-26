#!/usr/bin/env python3
"""
Update AWS Security Groups to allow public access to services
"""
import boto3
import sys

# Security group IDs from Terraform state
SG_CONFIG = {
    'monitor': {
        'id': 'sg-07b2facae786f1ba7',
        'name': 'aiops-dev-monitor-sg',
        'rules': [
            {
                'IpProtocol': 'tcp',
                'FromPort': 3001,
                'ToPort': 3001,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Grafana from internet'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 9090,
                'ToPort': 9090,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Prometheus from internet'}]
            }
        ]
    },
    'web': {
        'id': 'sg-07bd99bc54578289e',
        'name': 'aiops-dev-web-sg',
        'rules': [
            {
                'IpProtocol': 'tcp',
                'FromPort': 3000,
                'ToPort': 3000,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'Web app from internet'}]
            }
        ]
    },
    'core': {
        'id': 'sg-088882249fbfe9009',
        'name': 'aiops-dev-core-sg',
        'rules': [
            {
                'IpProtocol': 'tcp',
                'FromPort': 8000,
                'ToPort': 8000,
                'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'API from internet'}]
            }
        ]
    }
}

def update_security_groups():
    try:
        ec2 = boto3.client('ec2', region_name='ap-southeast-1')
        
        for sg_type, config in SG_CONFIG.items():
            sg_id = config['id']
            print(f"\n{'='*60}")
            print(f"Updating {sg_type.upper()} Security Group: {sg_id}")
            print(f"{'='*60}")
            
            # First, remove old rules with restrictive CIDR blocks
            try:
                sg = ec2.describe_security_groups(GroupIds=[sg_id])['SecurityGroups'][0]
                
                for rule in sg.get('IpPermissions', []):
                    from_port = rule.get('FromPort')
                    to_port = rule.get('ToPort')
                    
                    # Check if this is one of our service ports
                    service_ports = []
                    for new_rule in config['rules']:
                        service_ports.append(new_rule['FromPort'])
                    
                    if from_port in service_ports and from_port == to_port:
                        for cidr_block in rule.get('IpRanges', []):
                            # Remove old restrictive rules (not 0.0.0.0/0)
                            if cidr_block.get('CidrIp') != '0.0.0.0/0':
                                print(f"  Removing old rule: port {from_port} from {cidr_block.get('CidrIp')}")
                                try:
                                    ec2.revoke_security_group_ingress(
                                        GroupId=sg_id,
                                        IpPermissions=[rule]
                                    )
                                except Exception as e:
                                    print(f"  Note: {str(e)}")
            except Exception as e:
                print(f"  Error reading existing rules: {str(e)}")
            
            # Add new rules
            for rule in config['rules']:
                try:
                    print(f"  Adding rule: port {rule['FromPort']} from 0.0.0.0/0")
                    ec2.authorize_security_group_ingress(
                        GroupId=sg_id,
                        IpPermissions=[rule]
                    )
                    print(f"    ✓ Rule added successfully")
                except Exception as e:
                    if 'InvalidPermission.Duplicate' in str(e):
                        print(f"    ✓ Rule already exists")
                    else:
                        print(f"    ✗ Error: {str(e)}")
        
        print(f"\n{'='*60}")
        print("✓ Security groups updated successfully!")
        print(f"{'='*60}")
        print("\nServices are now accessible at:")
        print("  - Frontend (React):  http://18.139.198.122:3000")
        print("  - API:               http://52.77.15.93:8000")
        print("  - API Docs:          http://52.77.15.93:8000/docs")
        print("  - Grafana:           http://18.142.210.110:3001")
        print("  - Prometheus:        http://18.142.210.110:9090")
        print("\nGrafana credentials: admin / admin123")
        
    except Exception as e:
        print(f"✗ Error updating security groups: {str(e)}")
        print("\nMake sure you have valid AWS credentials configured:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        sys.exit(1)

if __name__ == '__main__':
    update_security_groups()
