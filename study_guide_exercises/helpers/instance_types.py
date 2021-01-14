from aws_cdk import aws_ec2 as ec2

R3_XLARGE = ec2.InstanceType.of(ec2.InstanceClass.MEMORY3,
                                ec2.InstanceSize.XLARGE2)

T2_MICRO = ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2,
                               ec2.InstanceSize.MICRO)

T2_NANO = ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2,
                              ec2.InstanceSize.NANO)
