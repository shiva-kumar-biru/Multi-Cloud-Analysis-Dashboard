"""
Multi-Cloud Pricing Comparison Dashboard

This script builds a Panel-based dashboard to compare instance pricing
across AWS, Azure, and GCP. Users can select region, vCPU, and memory,
then choose from matching instances and pricing models.

Supports On-Demand, Reserved, and Spot pricing models.

Author: [Shiva kumar Biru / Frankfurt University of Applied Sciences]
Date: [2025-06]
"""

import panel as pn
import boto3
import json
import pandas as pd
from datetime import datetime
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from google.oauth2 import service_account
from googleapiclient.discovery import build
from aws_pricing import fetch_aws_pricing
from azure_pricing import fetch_azure_pricing
from gcp_pricing import fetch_gcp_pricing
import time
import sys


pn.extension()

# ============================
# Global Constants and State
# ============================

## Note : Please chnage the gcp_project_id and the gcp_service_account_file , This you have to setup in the GCP console 
gcp_project_id = "my-test-project-461610"
gcp_service_account_file = "/Users/shivakumarbiru/Downloads/my-test-project-461610-9168517f59d4.json"

aws_data, azure_data, gcp_data = {}, {}, {}
pricing_labels_map, azure_pricing_labels, gcp_pricing_labels = {}, {}, {}
fetched_raw_terms = {}
spot_price_df = None
cached_region_name_map = {}
cached_azure_region_name_map = {}
cached_gcp_region_list = []
pricing_df = pd.DataFrame()  # Stores last comparison result
multi_cloud_plot = pn.pane.Bokeh()


# Widgets
cloud_services = pn.widgets.MultiSelect(name='Select Cloud Services', options=['AWS', 'Azure', 'GCP'], size=3)
region_selector = pn.widgets.Select(name="Select Region", options=[], width=250)
vcpu_input = pn.widgets.IntInput(name="vCPUs", width=100, step=1, start=1, disabled=True)
ram_input = pn.widgets.FloatInput(name="Memory (GB)", width=100, step=0.5, start=1.0, disabled=True)
instance_selector = pn.widgets.MultiSelect(name="Matching Instances", options=[], size=6,height=140)
pricing_model_selector = pn.widgets.MultiSelect(name='Select Pricing Models', options=[], size=6,height=140)
result_display = pn.pane.Markdown("### Select pricing models to compare.")
plot_pane = pn.pane.Bokeh()
compare_button = pn.widgets.Button(name="Compare", button_type="primary")
clear_button = pn.widgets.Button(name="Clear Chart", button_type="danger", visible=False)
reset_df_button = pn.widgets.Button(name="Reset Multi-Cloud Data", button_type="danger")

view_selector = pn.widgets.RadioButtonGroup(
    name="Compare By",
    options=["On-Demand", "Spot", "Reserved"],
    button_type="success"
)

# --- AWS Region & Instance Helpers ---
# AWS Regions
def get_aws_regions():
    start = time.time()
    ec2 = boto3.client("ec2", region_name="us-east-1")
    regions = ec2.describe_regions(AllRegions=True)['Regions']
    elapsed = time.time() - start

    regions_json = json.dumps(regions)
    size_kb = sys.getsizeof(regions_json) / 1024
    size_mb = size_kb / 1024

    print(f"\n AWS region fetch")
    print(f" Regions fetched: {len(regions)}")
    print(f" Data size: {size_kb:.2f} KB (~{size_mb:.2f} MB)")
    print(f" Time taken: {elapsed:.2f} seconds")

    return sorted([r['RegionName'] for r in regions if r['OptInStatus'] in ('opt-in-not-required', 'opted-in')])

# Azure Regions
def get_azure_regions(subscription_id):
    global cached_azure_skus
    start = time.time()

    client = ComputeManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=subscription_id,
    )

    # Fetch and cache SKUs
    cached_azure_skus = list(client.resource_skus.list())
    elapsed = time.time() - start

    skus_json = json.dumps([sku.as_dict() for sku in cached_azure_skus])
    size_kb = sys.getsizeof(skus_json) / 1024
    size_mb = size_kb / 1024

    print(f"\n Azure region fetch")
    print(f"SKUs fetched: {len(cached_azure_skus)}")
    print(f" Data size: {size_kb:.2f} KB (~{size_mb:.2f} MB)")
    print(f" Time taken: {elapsed:.2f} seconds")

    region_display_map = {}
    for sku in cached_azure_skus:
        if sku.resource_type == "virtualMachines":
            for loc in sku.locations:
                formatted = loc.lower().replace(" ", "")
                region_display_map[formatted] = loc

    return dict(sorted(region_display_map.items()))


# GCP Regions
def get_gcp_regions(project_id: str, service_account_file: str):
    start = time.time()
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    compute = build('compute', 'v1', credentials=credentials)
    request = compute.regions().list(project=project_id)
    response = request.execute()
    elapsed = time.time() - start

    regions = response.get('items', [])
    regions_json = json.dumps(regions)
    size_kb = sys.getsizeof(regions_json) / 1024
    size_mb = size_kb / 1024

    print(f"\n GCP region fetch")
    print(f" Regions fetched: {len(regions)}")
    print(f" Data size: {size_kb:.2f} KB (~{size_mb:.2f} MB)")
    print(f" Time taken: {elapsed:.2f} seconds")

    return [r['name'] for r in regions]

# AWS Friendly Region Names
def get_static_aws_region_name_map():
    return {
        "us-east-1": "US East (N. Virginia)",
        "us-east-2": "US East (Ohio)",
        "us-west-1": "US West (N. California)",
        "us-west-2": "US West (Oregon)",
        "af-south-1": "Africa (Cape Town)",
        "ap-east-1": "Asia Pacific (Hong Kong)",
        "ap-south-1": "Asia Pacific (Mumbai)",
        "ap-northeast-3": "Asia Pacific (Osaka)",
        "ap-northeast-2": "Asia Pacific (Seoul)",
        "ap-southeast-1": "Asia Pacific (Singapore)",
        "ap-southeast-2": "Asia Pacific (Sydney)",
        "ap-northeast-1": "Asia Pacific (Tokyo)",
        "ca-central-1": "Canada (Central)",
        "eu-central-1": "EU (Frankfurt)",
        "eu-west-1": "EU (Ireland)",
        "eu-west-2": "EU (London)",
        "eu-south-1": "EU (Milan)",
        "eu-west-3": "EU (Paris)",
        "eu-north-1": "EU (Stockholm)",
        "me-south-1": "Middle East (Bahrain)",
        "sa-east-1": "South America (São Paulo)",
        "me-central-1": "Middle East (UAE)",
        "eu-central-2": "EU (Zurich)",
        "ap-south-2": "Asia Pacific (Hyderabad)",
        "ap-southeast-3": "Asia Pacific (Jakarta)",
    }

def get_exact_instance_types(region, exact_vcpus, exact_memory_gib):
    start = time.time()
    ec2 = boto3.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_instance_types")
    all_data = []

    for page in paginator.paginate():
        all_data.extend(page["InstanceTypes"])

    elapsed = time.time() - start
    json_blob = json.dumps(all_data)
    size_kb = sys.getsizeof(json_blob) / 1024
    size_mb = size_kb / 1024

    print(f"\n AWS instance type fetch")
    print(f" Instance types fetched: {len(all_data)}")
    print(f" Data size: {size_kb:.2f} KB (~{size_mb:.2f} MB)")
    print(f" Time taken: {elapsed:.2f} seconds")

    matching_types = []
    for itype in all_data:
        instance_type = itype["InstanceType"]
        vcpus = itype["VCpuInfo"]["DefaultVCpus"]
        memory_gib = round(itype["MemoryInfo"]["SizeInMiB"] / 1024, 2)
        if vcpus == exact_vcpus and memory_gib == exact_memory_gib:
            matching_types.append(instance_type)

    return matching_types


def get_matching_azure_vm_sizes(region: str, required_cores: int, required_memory_gb: float, subscription_id: str):
    global cached_azure_skus

    if not cached_azure_skus:
        print(" Azure SKUs not cached. Fetching now...")
        client = ComputeManagementClient(
            credential=DefaultAzureCredential(),
            subscription_id=subscription_id,
        )
        cached_azure_skus = list(client.resource_skus.list())

    skus = cached_azure_skus

    #  Start timer AFTER cache load
    start = time.time()

    matching_vms = []
    for sku in skus:
        if sku.resource_type != "virtualMachines":
            continue
        if region not in sku.locations:
            continue

        capabilities = {cap.name: cap.value for cap in sku.capabilities}
        try:
            cores = int(capabilities.get("vCPUs", 0))
            memory = float(capabilities.get("MemoryGB", 0.0))
        except ValueError:
            continue

        if cores == required_cores and memory == required_memory_gb:
            matching_vms.append(sku.name)

    elapsed = time.time() - start
    print(f"\n Azure VM size match complete")
    print(f" Matched VM sizes: {len(matching_vms)}")
    print(f" Matching time: {elapsed:.2f} seconds")

    return matching_vms

def get_matching_gcp_vm_types(region, vcpus_required, memory_required_gb):
    start = time.time()
    credentials = service_account.Credentials.from_service_account_file(
        gcp_service_account_file,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    compute = build('compute', 'v1', credentials=credentials)
    zone = f"{region}-a"

    request = compute.machineTypes().list(project=gcp_project_id, zone=zone)
    response = request.execute()
    elapsed = time.time() - start

    machine_types = response.get("items", [])
    json_blob = json.dumps(machine_types)
    size_kb = sys.getsizeof(json_blob) / 1024
    size_mb = size_kb / 1024

    print(f"\n GCP machine type fetch")
    print(f" Machine types fetched: {len(machine_types)}")
    print(f" Data size: {size_kb:.2f} KB (~{size_mb:.2f} MB)")
    print(f" Time taken: {elapsed:.2f} seconds")

    matching = []
    for mt in machine_types:
        name = mt.get("name", "")
        cpus = mt.get("guestCpus")
        mem = round(mt.get("memoryMb", 0) / 1024, 1)
        if cpus == vcpus_required and mem == memory_required_gb:
            matching.append(name)

    return matching

# --- Pricing Summary Logic ---
def summarize_selected_pricing(selected_models):
    summary = "### Detailed Pricing Info\n"
    for model in selected_models:
        info = pricing_labels_map.get(model, {})
        term_type = info.get('termType', '')
        offering_filter = info.get('offeringClass', '')

        if term_type == 'Spot':
            if spot_price_df is not None and not spot_price_df.empty:
                avg = spot_price_df['Price'].mean()
                latest = spot_price_df.iloc[-1]
                summary += f"\n#### Spot\n- Current Price: ${latest['Price']:.4f} (as of {latest['Time']})\n- 7-day Avg: ${avg:.4f}\n"

        elif term_type.lower() == 'ondemand':
            summary += "\n#### OnDemand\n"
            for term_id, term in fetched_raw_terms.get(term_type, {}).items():
                for dim in term.get('priceDimensions', {}).values():
                    price = float(dim['pricePerUnit'].get('USD', 0.0))
                    desc = dim.get('description', '')
                    unit = dim.get('unit', '')
                    summary += f"- ${price:.4f} per {unit} | {desc}\n"

        elif term_type.lower() == 'reserved':
            summary += f"\n#### Reserved - {offering_filter}\n"
            grouped = {'1yr': {}, '3yr': {}}

            for term_id, term in fetched_raw_terms.get(term_type, {}).items():
                attrs = term.get('termAttributes', {})
                if attrs.get('OfferingClass', '') != offering_filter:
                    continue

                lease = attrs.get('LeaseContractLength', '')
                purchase = attrs.get('PurchaseOption', '')

                upfront = None
                hourly = None

                for dim in term.get('priceDimensions', {}).values():
                    price = float(dim['pricePerUnit'].get('USD', 0.0))
                    unit = dim.get('unit', '').lower()

                    if unit == 'quantity':
                        upfront = price
                    elif 'hr' in unit or 'hour' in unit:
                        hourly = price

                upfront = upfront if upfront is not None else 0.0
                hourly = hourly if hourly is not None else 0.0

                if lease in grouped:
                    grouped[lease][purchase] = {
                        'upfront': upfront,
                        'hourly': hourly
                    }

            for lease_term, options in grouped.items():
                summary += f"\n**Term: {lease_term.replace('yr', ' Year')}**\n"
                for purchase_type in ['All Upfront', 'No Upfront', 'Partial Upfront']:
                    if purchase_type in options:
                        plan = options[purchase_type]
                        summary += f"\n*{purchase_type}*\n"
                        summary += f"-  Upfront: ${plan['upfront']:.2f}\n"
                        summary += f"- Listed Hourly: ${plan['hourly']:.4f} / hour\n"

                        if plan['hourly'] == 0.0 and plan['upfront'] > 0.0:
                            months = 12 if '1yr' in lease_term else 36
                            total_hours = months * 720
                            effective = plan['upfront'] / total_hours
                            summary += f"-  Effective Hourly (from upfront only): ${effective:.4f} / hour\n"

        elif model in azure_pricing_labels:
            info = azure_pricing_labels[model]
            raw_price = info['raw_price']
            term = info['term']
            payment = info['payment']
            sku = info.get('sku', 'Unknown SKU')
            region = info.get('region', 'Unknown Region')

            months = 12 if '1 year' in term.lower() else 36 if '3 year' in term.lower() else 1
            hourly = raw_price / (months * 730) if months > 1 else raw_price
            monthly = hourly * 730

            summary += f"\n#### Azure - {model}\n"
            summary += f"- ${hourly:.4f} per Hour | {model} for {sku} in {region}\n"
            summary += f"- Monthly (730 hrs): ${monthly:.2f}"
            if term != '-' or payment != '-':
                summary += f" | Term: {term}"
                if payment != '-':
                    summary += f", Payment: {payment}"
            summary += "\n"
            
        elif model in gcp_pricing_labels:
            try:
                entry = gcp_pricing_labels[model]
                hourly = entry['raw_price']
                monthly = hourly * 730
                summary += f"\n#### GCP - {model}\n"
                summary += f"- Instance Type: `{entry['instance_type']}`\n"
                summary += f"- Region: `{entry['region']}`\n"
                summary += f"- Hourly Price: ${hourly:.4f}\n"
                summary += f"- Monthly (730 hrs): ${monthly:.2f}\n"
            except KeyError as e:
                summary += f"\n Error: Missing data for `{model}` - {e}\n"



    return summary.strip()

# --- Callback Handlers ---
def update_instance_selector(event=None):
    selected_region = region_selector.value
    vcpus = vcpu_input.value
    ram = ram_input.value
    cloud = cloud_services.value

    if not selected_region or not vcpus or not ram:
        instance_selector.options = []
        return

    try:
        if 'AWS' in cloud:
            matching = get_exact_instance_types(selected_region, vcpus, ram)
        elif 'Azure' in cloud:
            matching = get_matching_azure_vm_sizes(
                selected_region, vcpus, ram,
                subscription_id="3678f0d5-8b1b-42cf-a148-b0d220f01c55"
            )
        elif 'GCP' in cloud:
            matching = get_matching_gcp_vm_types(
                selected_region, vcpus, ram
            )

        else:
            matching = []

        instance_selector.options = matching
    except Exception as e:
        instance_selector.options = []
        result_display.object = f"### Error fetching instance types: {str(e)}"


def update_pricing_models_for_instance(event):
    global aws_data, pricing_labels_map, fetched_raw_terms, spot_price_df
    global azure_data, azure_pricing_labels
    global gcp_data, gcp_pricing_labels
    global cached_azure_region_name_map  

    selected_instances = event.new
    if not selected_instances or not region_selector.value:
        pricing_model_selector.options = []
        return

    selected_instance = selected_instances[0]
    print(selected_instance)
    region_ui = region_selector.value
    print(region_ui)
    cloud = cloud_services.value

    try:
        if 'AWS' in cloud:
            aws_region_name = cached_region_name_map.get(region_ui, region_ui)
            result_display.object = f"### Fetching AWS pricing for {selected_instance} in {aws_region_name}..."
            aws_data, pricing_labels_map, fetched_raw_terms, spot_price_df = fetch_aws_pricing(
                instance_type=selected_instance, region=aws_region_name
            )
            pricing_model_selector.options = list(aws_data.keys())
            result_display.object = f"### Found {len(aws_data)} pricing models for {selected_instance} in {aws_region_name}"

        elif 'Azure' in cloud:
        # Map the display name to Azure's internal region key
            region_internal = None
            for key, value in cached_azure_region_name_map.items():
                if value.strip().lower() == region_ui.strip().lower():
                    region_internal = key
                    break

            if not region_internal:
                result_display.object = f"### Unable to map Azure region: {region_ui}"
                return

            result_display.object = f"### Fetching Azure pricing for {selected_instance} in {region_internal}..."
            azure_data, azure_pricing_labels = fetch_azure_pricing(sku=selected_instance, region=region_internal)
            print(f" Azure pricing labels: {azure_pricing_labels}")  # DEBUG LINE
            pricing_model_selector.options = list(azure_data.keys())
            result_display.object = f"### Found {len(azure_data)} pricing models for {selected_instance} in {region_internal}"

        elif 'GCP' in cloud:
            result_display.object = f"### Fetching GCP pricing for {selected_instance}..."
            gcp_data, gcp_pricing_labels = fetch_gcp_pricing(instance_type=selected_instance, region=region_ui,cpu=vcpu_input.value,ram=ram_input.value)
            pricing_model_selector.options = list(gcp_data.keys())
            result_display.object = f"### Found {len(gcp_data)} pricing models for {selected_instance} in {region_ui}"    

    except Exception as e:
        pricing_model_selector.options = []
        result_display.object = f"### Pricing fetch failed: {str(e)}"


def update_pricing_models(cloud_selection):
    global azure_data, azure_pricing_labels
    global gcp_data, gcp_pricing_labels
    global cached_region_name_map
    global cached_azure_region_name_map 

    #  FULL RESET on cloud switch
    region_selector.options = []
    region_selector.value = None
    instance_selector.options = []
    pricing_model_selector.options = []
    vcpu_input.value = 0
    ram_input.value = 0
    vcpu_input.disabled = True
    ram_input.disabled = True

def update_pricing_models(cloud_selection):
    global azure_data, azure_pricing_labels
    global gcp_data, gcp_pricing_labels
    global cached_region_name_map
    global cached_azure_region_name_map 

    # 🔁 FULL RESET on cloud switch
    region_selector.options = []
    region_selector.value = None
    instance_selector.options = []
    pricing_model_selector.options = []
    vcpu_input.value = 0
    ram_input.value = 0.0
    vcpu_input.disabled = True
    ram_input.disabled = True

    if 'AWS' in cloud_selection:
        result_display.object = "### Initializing AWS region list..."
        try:
            region_selector.value = None  # Clear value first
            region_selector.options = ['-- Select a Region --'] + get_aws_regions()

            cached_region_name_map = get_static_aws_region_name_map()

            result_display.object = "### ✅ AWS regions loaded. Please select a region."
            print(" Cached AWS Region Name Map:")
            for code, name in cached_region_name_map.items():
                print(f"{code} → {name}")

        except Exception as e:
            result_display.object = f"### AWS error: {str(e)}"


    if 'Azure' in cloud_selection:
        result_display.object = "### Fetching Azure regions..."
        try:
            region_map = get_azure_regions(subscription_id="57f76510-1b03-4666-a9df-9fada6e1d00e")
            cached_azure_region_name_map = region_map
            region_selector.value = None
            region_selector.options = ['-- Select a Region --'] + list(region_map.values())
            vcpu_input.disabled = True
            ram_input.disabled = True
            result_display.object = "### ✅ Azure regions loaded. Please select a region."

        except Exception as e:
            result_display.object = f"### Azure error: {str(e)}"


    if 'GCP' in cloud_selection:
        result_display.object = "### Fetching GCP regions..."
        try:
            cached_gcp_region_list = get_gcp_regions(gcp_project_id, gcp_service_account_file)
            region_selector.value = None
            region_selector.options = ['-- Select a Region --'] + cached_gcp_region_list

            vcpu_input.disabled = True
            ram_input.disabled = True
            result_display.object = "### ✅ GCP regions loaded. Please select a region."
        except Exception as e:
            result_display.object = f"### GCP error: {str(e)}"

    # Reset inputs and dropdowns regardless of cloud
    instance_selector.options = []
    pricing_model_selector.options = []
    vcpu_input.value = 0
    ram_input.value = 0
    vcpu_input.disabled = True
    ram_input.disabled = True
    region_selector.value = '-- Select a Region --'



def on_cloud_selection_change(event):
    update_pricing_models(event.new)

def on_region_selected(event):
    if region_selector.value and "-- Select" not in region_selector.value:
        vcpu_input.disabled = False
        ram_input.disabled = False
        update_instance_selector()
    else:
        vcpu_input.disabled = True
        ram_input.disabled = True
        instance_selector.options = []
        pricing_model_selector.options = []


def on_pricing_model_selected(event):
    selected = list(event.new)
    print(f" Selected models: {selected}")  # DEBUG LINE
    if not selected:
        result_display.object = "### No pricing model selected."
    else:
        result_display.object = summarize_selected_pricing(selected)



def compare_prices(event=None):
    selected = list(pricing_model_selector.value)
    if not selected:
        result_display.object = "### Please select at least one pricing model."
        plot_pane.object = None
        return

    result_display.object = "### Pricing models selected. Showing monthly cost comparison."

    prices = {}
    rows = []

    for model in selected:
        # --- AWS ---
        if model in pricing_labels_map:
            info = pricing_labels_map[model]
            term_type = info.get('termType', '')
            offering_filter = info.get('offeringClass', '')

            if term_type == 'Spot' and spot_price_df is not None and not spot_price_df.empty:
                avg_spot = spot_price_df['Price'].mean()
                prices['AWS Spot'] = round(avg_spot * 730, 2)

            elif term_type.lower() == 'ondemand':
                for term in fetched_raw_terms[term_type].values():
                    for dim in term.get('priceDimensions', {}).values():
                        price = float(dim['pricePerUnit'].get('USD', 0.0))
                        prices['AWS OnDemand'] = round(price * 730, 2)

            elif term_type.lower() == 'reserved':
                reserved_label = 'Convertible' if 'convertible' in model.lower() else 'Standard'
                for term in fetched_raw_terms[term_type].values():
                    attrs = term.get('termAttributes', {})
                    if attrs.get('OfferingClass', '') != offering_filter:
                        continue
                    lease = attrs.get('LeaseContractLength', '')
                    purchase = attrs.get('PurchaseOption', '')
                    upfront = 0.0
                    hourly = 0.0
                    for dim in term.get('priceDimensions', {}).values():
                        unit = dim.get('unit', '').lower()
                        price = float(dim['pricePerUnit'].get('USD', 0.0))
                        if unit == 'quantity':
                            upfront = price
                        elif 'hr' in unit or 'hour' in unit:
                            hourly = price
                    months = 12 if '1yr' in lease else 36
                    monthly_cost = (upfront / months) + (hourly * 730)
                    label = f"AWS RI {reserved_label} {lease} {purchase}"
                    prices[label] = round(monthly_cost, 2)

        # --- Azure ---
        elif model in azure_pricing_labels:
            info = azure_pricing_labels[model]
            raw_price = info['raw_price']
            term = info['term'].lower()
            months = 12 if '1 year' in term else 36 if '3 year' in term else 1
            hourly = raw_price / (months * 730) if months > 1 else raw_price
            monthly = hourly * 730
            prices[f"Azure {model}"] = round(monthly, 2)

        # --- GCP ---
        elif model in gcp_pricing_labels:
            entry = gcp_pricing_labels[model]
            hourly = entry['raw_price']
            monthly = hourly * 730
            prices[f"GCP {model}"] = round(monthly, 2)

    if not prices:
        result_display.object = "### No pricing data available for selected models."
        plot_pane.object = None
        return

    for label, monthly_cost in prices.items():
        cloud = "AWS" if "AWS" in label else "Azure" if "Azure" in label else "GCP" if "GCP" in label else "Unknown"
        label_lower = label.lower()

        if "spot" in label_lower:
            ptype = "Spot"
        elif "reserved" in label_lower or "ri" in label_lower or "commit" in label_lower:
            ptype = "Reserved"
        elif "on-demand" in label_lower or "ondemand" in label_lower or "pay-as-you-go" in label_lower:
            ptype = "On-Demand"
        else:
            ptype = "Other"

        rows.append({
            "Model": label,
            "Monthly Cost (USD)": monthly_cost,
            "Cloud": cloud,
            "Region": region_selector.value,
            "Pricing Type": ptype,
            "Pricing Type Normalized": ptype  # 🔧 for accurate filtering
        })

    global pricing_df
    new_df = pd.DataFrame(rows)
    pricing_df = pd.concat([pricing_df, new_df], ignore_index=True).drop_duplicates(subset=["Model", "Cloud", "Region"])

    print(" Multi-Cloud Pricing DataFrame:")
    print(pricing_df)

    # Create Bokeh bar chart
    source = ColumnDataSource(data={'models': list(prices.keys()), 'prices': list(prices.values())})
    p = figure(
        x_range=list(prices.keys()),
        height=400,
        title="Cloud Pricing Comparison (Monthly)",
        tools="hover",
        tooltips=[("Model", "@models"), ("Monthly Cost", "@prices{$0.00}")]
    )
    p.vbar(x='models', top='prices', width=0.9, source=source)
    p.xaxis.major_label_orientation = 1
    p.xaxis.axis_label = "Pricing Models"
    p.yaxis.axis_label = "Monthly Cost (USD)"
    plot_pane.object = p
    clear_button.visible = True


def update_cloud_comparison(event=None):
    global pricing_df
    selection = view_selector.value
    if pricing_df.empty:
        result_display.object = "ℹ️ Please run a pricing comparison first."
        multi_cloud_plot.object = None
        return

    # 🛠️ Improved filtering with normalization and case-insensitive match
    df = pricing_df[
        pricing_df["Pricing Type Normalized"]
        .astype(str)
        .str.strip()
        .str.casefold()
        == selection.strip().casefold()
    ]

    # 🧪 Optional debug print
    print(f" Selection: {selection}")
    print(f" Rows found: {len(df)}")
    print(df[["Model", "Pricing Type Normalized"]])

    if df.empty:
        multi_cloud_plot.object = None
        result_display.object = f"⚠️ No entries found for {selection}"
        return

    #  Plotting logic
    source = ColumnDataSource(data={
        "models": df["Model"],
        "prices": df["Monthly Cost (USD)"],
        "cloud": df["Cloud"],
        "region": df["Region"]
    })

    p = figure(
        x_range=list(df["Model"]),
        height=350,
        title=f"{selection} Pricing Across Clouds",
        tools="hover",
        tooltips=[
            ("Model", "@models"),
            ("Cloud", "@cloud"),
            ("Region", "@region"),
            ("Monthly", "@prices{$0.00}")
        ]
    )

    p.vbar(x="models", top="prices", width=0.9, source=source)
    p.xaxis.major_label_orientation = 1
    p.xaxis.axis_label = "Cloud + Pricing Model"
    p.yaxis.axis_label = "Monthly Cost (USD)"
    multi_cloud_plot.object = p






def clear_chart(event=None):
    plot_pane.object = None
    result_display.object = "### Select pricing models to compare."
    clear_button.visible = False

def clear_plot_on_deselect(event):
    if len(event.new) == 0:
        clear_chart()

def reset_pricing_df(event):
    global pricing_df
    pricing_df = pd.DataFrame()
    result_display.object = "✅ Cleared multi-cloud pricing data."


view_selector.param.watch(update_cloud_comparison, 'value')
compare_button.on_click(compare_prices)
clear_button.on_click(clear_chart)
# --- Watchers ---
cloud_services.param.watch(on_cloud_selection_change, 'value')
region_selector.param.watch(on_region_selected, 'value')
vcpu_input.param.watch(update_instance_selector, 'value')
ram_input.param.watch(update_instance_selector, 'value')
instance_selector.param.watch(update_pricing_models_for_instance, 'value')
pricing_model_selector.param.watch(on_pricing_model_selected, 'value')
reset_df_button.on_click(reset_pricing_df)


template = pn.template.BootstrapTemplate(
    title="Cloud Cost Analysis Dashboard",
    site="Frankfurt University of Applied Sciences",
    header_background='#6424db',
    sidebar_width=350,
    sidebar=pn.Column(
        pn.pane.Markdown("### Select Cloud Provider"),
        cloud_services,

        pn.pane.Markdown("### Select Region"),
        region_selector,

        pn.Row(vcpu_input, ram_input, sizing_mode="stretch_width"),

        pn.pane.Markdown("### Matching Instances"),
        instance_selector,

        pn.pane.Markdown("### Select Pricing Models"),
        pricing_model_selector,

        compare_button,
        clear_button
    ),
    main=[
        pn.Row(
            pn.Column(
                pn.pane.Markdown("## 📊 Selected Cloud Pricing Summary"),
                result_display,
                plot_pane,
                sizing_mode="stretch_width",
                width_policy="max"
            ),
            pn.Column(
                pn.pane.Markdown("## 🌐 Multi-Cloud Pricing Comparison"),
                view_selector,
                multi_cloud_plot,
                reset_df_button,
                sizing_mode="stretch_width",
                width_policy="max"
            ),
            sizing_mode="stretch_width"
        )
    ]
)

template.servable()



