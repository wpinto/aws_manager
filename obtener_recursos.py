def obtener_instancias_ec2(ec2_client):
    """Obtiene información detallada de instancias EC2"""
    try:
        response = ec2_client.describe_instances()
        instancias = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                name = "Sin nombre"
                if "Tags" in instance:
                    for tag in instance["Tags"]:
                        if tag["Key"] == "Name":
                            name = tag["Value"]
                            break
                
                launch_time = instance.get("LaunchTime", "").strftime("%Y-%m-%d %H:%M") if instance.get("LaunchTime") else "N/A"
                
                # Información adicional para detalles
                vpc_id = instance.get("VpcId", "N/A")
                subnet_id = instance.get("SubnetId", "N/A")
                security_groups = ", ".join([sg.get("GroupName", sg.get("GroupId", "")) for sg in instance.get("SecurityGroups", [])])
                public_ip = instance.get("PublicIpAddress", "N/A")
                key_name = instance.get("KeyName", "N/A")
                architecture = instance.get("Architecture", "N/A")
                hypervisor = instance.get("Hypervisor", "N/A")
                platform = instance.get("Platform", "Linux/UNIX")
                
                instancias.append({
                    "id": instance["InstanceId"],
                    "name": name,
                    "state": instance["State"]["Name"],
                    "type": instance.get("InstanceType", "Desconocido"),
                    "launch_time": launch_time,
                    "private_ip": instance.get("PrivateIpAddress", "N/A"),
                    "public_ip": public_ip,
                    "vpc_id": vpc_id,
                    "subnet_id": subnet_id,
                    "security_groups": security_groups,
                    "key_name": key_name,
                    "architecture": architecture,
                    "hypervisor": hypervisor,
                    "platform": platform,
                    "availability_zone": instance.get("Placement", {}).get("AvailabilityZone", "N/A"),
                    "state_reason": instance.get("StateReason", {}).get("Message", "N/A"),
                    "tags": instance.get("Tags", [])
                })
        return instancias
    except Exception as e:
        raise Exception(f"Error al obtener instancias EC2: {str(e)}")

def obtener_instancias_rds(rds_client):
    """Obtiene información detallada de instancias RDS"""
    try:
        response = rds_client.describe_db_instances()
        instancias = []
        for db in response["DBInstances"]:
            # Información adicional para detalles
            storage_type = db.get("StorageType", "N/A")
            allocated_storage = db.get("AllocatedStorage", "N/A")
            max_allocated_storage = db.get("MaxAllocatedStorage", "N/A")
            backup_retention = db.get("BackupRetentionPeriod", "N/A")
            multi_az = "Sí" if db.get("MultiAZ", False) else "No"
            publicly_accessible = "Sí" if db.get("PubliclyAccessible", False) else "No"
            endpoint = db.get("Endpoint", {}).get("Address", "N/A") if db.get("Endpoint") else "N/A"
            port = db.get("Endpoint", {}).get("Port", "N/A") if db.get("Endpoint") else "N/A"
            vpc_security_groups = ", ".join([sg.get("VpcSecurityGroupId", "") for sg in db.get("VpcSecurityGroups", [])])
            
            instancias.append({
                "id": db["DBInstanceIdentifier"],
                "name": db.get("DBName", db["DBInstanceIdentifier"]),
                "state": db["DBInstanceStatus"],
                "engine": f"{db.get('Engine', 'Desconocido')} {db.get('EngineVersion', 'N/A')}",
                "class": db.get("DBInstanceClass", "N/A"),
                "storage_type": storage_type,
                "allocated_storage": allocated_storage,
                "max_allocated_storage": max_allocated_storage,
                "backup_retention": backup_retention,
                "multi_az": multi_az,
                "publicly_accessible": publicly_accessible,
                "endpoint": endpoint,
                "port": port,
                "vpc_security_groups": vpc_security_groups,
                "availability_zone": db.get("AvailabilityZone", "N/A"),
                "creation_time": db.get("InstanceCreateTime", "").strftime("%Y-%m-%d %H:%M") if db.get("InstanceCreateTime") else "N/A"
            })
        return instancias
    except Exception as e:
        raise Exception(f"Error al obtener instancias RDS: {str(e)}")
    
# Agregar esta función a tu archivo obtener_recursos.py

def obtener_security_groups(ec2_client):
    """
    Obtiene todos los Security Groups de la cuenta AWS
    """
    try:
        response = ec2_client.describe_security_groups()
        security_groups = []
        
        for sg in response['SecurityGroups']:
            # Obtener nombre de las tags si existe
            name = sg['GroupName']
            for tag in sg.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            
            # Formatear reglas de ingreso
            ingress_rules = []
            for rule in sg['IpPermissions']:
                protocol = rule.get('IpProtocol', '')
                if protocol == '-1':
                    port_range = 'All'
                elif 'FromPort' in rule and 'ToPort' in rule:
                    if rule['FromPort'] == rule['ToPort']:
                        port_range = str(rule['FromPort'])
                    else:
                        port_range = f"{rule['FromPort']}-{rule['ToPort']}"
                else:
                    port_range = 'All'
                
                # Fuentes
                sources = []
                for ip_range in rule.get('IpRanges', []):
                    sources.append(ip_range['CidrIp'])
                for sg_ref in rule.get('UserIdGroupPairs', []):
                    sources.append(f"sg:{sg_ref['GroupId']}")
                for prefix in rule.get('PrefixListIds', []):
                    sources.append(f"pl:{prefix['PrefixListId']}")
                
                if sources:
                    ingress_rules.append(f"{protocol}:{port_range} from {', '.join(sources)}")
            
            # Formatear reglas de egreso
            egress_rules = []
            for rule in sg['IpPermissionsEgress']:
                protocol = rule.get('IpProtocol', '')
                if protocol == '-1':
                    port_range = 'All'
                elif 'FromPort' in rule and 'ToPort' in rule:
                    if rule['FromPort'] == rule['ToPort']:
                        port_range = str(rule['FromPort'])
                    else:
                        port_range = f"{rule['FromPort']}-{rule['ToPort']}"
                else:
                    port_range = 'All'
                
                # Destinos
                destinations = []
                for ip_range in rule.get('IpRanges', []):
                    destinations.append(ip_range['CidrIp'])
                for sg_ref in rule.get('UserIdGroupPairs', []):
                    destinations.append(f"sg:{sg_ref['GroupId']}")
                for prefix in rule.get('PrefixListIds', []):
                    destinations.append(f"pl:{prefix['PrefixListId']}")
                
                if destinations:
                    egress_rules.append(f"{protocol}:{port_range} to {', '.join(destinations)}")
            
            sg_data = {
                "id": sg['GroupId'],
                "name": name,
                "group_name": sg['GroupName'],
                "vpc_id": sg.get('VpcId', 'EC2-Classic'),
                "description": sg['Description'],
                "owner_id": sg['OwnerId'],
                "ingress_rules_count": len(sg['IpPermissions']),
                "egress_rules_count": len(sg['IpPermissionsEgress']),
                "ingress_rules": ingress_rules,
                "egress_rules": egress_rules,
                "raw_ingress": sg['IpPermissions'],
                "raw_egress": sg['IpPermissionsEgress'],
                "tags": sg.get('Tags', [])
            }
            
            security_groups.append(sg_data)
        
        return security_groups
        
    except Exception as e:
        print(f"Error obteniendo Security Groups: {e}")
        return []


def obtener_vpcs_con_nombres(ec2_client):
    """
    Obtiene todas las VPCs con sus nombres de tags
    """
    try:
        response = ec2_client.describe_vpcs()
        vpcs = {}
        
        for vpc in response['Vpcs']:
            vpc_id = vpc['VpcId']
            vpc_name = "Sin nombre"
            
            # Buscar tag Name
            for tag in vpc.get('Tags', []):
                if tag['Key'] == 'Name':
                    vpc_name = tag['Value']
                    break
            
            # Si no tiene nombre, usar información de la VPC
            if vpc_name == "Sin nombre":
                if vpc.get('IsDefault', False):
                    vpc_name = "VPC por defecto"
                else:
                    vpc_name = f"VPC {vpc_id}"
            
            vpcs[vpc_id] = {
                'name': vpc_name,
                'cidr': vpc.get('CidrBlock', ''),
                'is_default': vpc.get('IsDefault', False),
                'state': vpc.get('State', ''),
                'dhcp_options_id': vpc.get('DhcpOptionsId', ''),
                'instance_tenancy': vpc.get('InstanceTenancy', '')
            }
        
        return vpcs
        
    except Exception as e:
        print(f"Error obteniendo VPCs: {e}")
        return {}