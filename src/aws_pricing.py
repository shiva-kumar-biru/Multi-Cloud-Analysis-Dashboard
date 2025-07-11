import boto3
import json
import pandas as pd
from datetime import datetime, timedelta

HOURS_PER_MONTH = 730
# def fetch_aws_pricing(instance_type="t3a.2xlarge", region="US East (N. Virginia)", os='Linux'):
def fetch_aws_pricing(instance_type:str, region:str, os='Linux'):
    client = boto3.client('pricing', region_name='us-east-1')
    product_response = client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os},
            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
        ],
        FormatVersion='aws_v1',
        MaxResults=100
    )

    if not product_response['PriceList']:
        # return {}, {}, pd.DataFrame()
        return {}, {}, {}, pd.DataFrame()


    product = json.loads(product_response['PriceList'][0])
    sku = product['product']['sku']

    pricing_response = client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[{'Type': 'TERM_MATCH', 'Field': 'sku', 'Value': sku}],
        MaxResults=100
    )

    product_data = json.loads(pricing_response['PriceList'][0])
    raw_terms = product_data.get('terms', {})
    pricing_map = {}

    labels_map = {}
    for term_type in raw_terms:
        for term_id, term_data in raw_terms[term_type].items():
            attrs = term_data.get('termAttributes', {})
            offering = attrs.get('OfferingClass', 'Default')
            key = f"{term_type.capitalize()} - {offering}"
            pricing_map[key] = 0
            labels_map[key] = {"termType": term_type, "offeringClass": offering}

    ec2 = boto3.client('ec2')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)
    spot_response = ec2.describe_spot_price_history(
        InstanceTypes=[instance_type],
        ProductDescriptions=['Linux/UNIX'],
        StartTime=start_time,
        EndTime=end_time,
        MaxResults=1000
    )
    spot_data = spot_response['SpotPriceHistory']
    spot_df = pd.DataFrame([{ 'Time': entry['Timestamp'], 'Price': float(entry['SpotPrice']) } for entry in spot_data])
    spot_df.sort_values(by='Time', inplace=True)

    if not spot_df.empty:
        avg = spot_df['Price'].mean()
        pricing_map['Spot'] = round(avg * HOURS_PER_MONTH, 2)
        labels_map['Spot'] = {"termType": "Spot"}

    return pricing_map, labels_map, raw_terms, spot_df



