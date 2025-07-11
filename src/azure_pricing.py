# azure_pricing.py (modified to integrate into GUI)
import requests
import json

HOURS_PER_MONTH = 730

def extract_payment_option(sku_name):
    if not sku_name:
        return '-'
    sku_name = sku_name.lower()
    for option in ['allupfront', 'noupfront', 'partialupfront']:
        if option in sku_name:
            return option.title().replace("upfront", "Upfront")
    return '-'

def determine_model(item):
    reservation_term = item.get('reservationTerm', '').lower()
    sku_name = item.get('skuName', '').lower()
    meter_name = item.get('meterName', '').lower()

    if 'spot' in meter_name or 'spot' in sku_name:
        return 'Spot'
    if 'low priority' in meter_name or 'low priority' in sku_name:
        return 'Low Priority'
    if '1 year' in reservation_term:
        return 'Reserved 1YR'
    if '3 year' in reservation_term or '3 years' in reservation_term:
        return 'Reserved 3YR'
    if reservation_term == '-' or reservation_term == '':
        return 'On-Demand'
    return 'Other'

def is_linux_item(item):
    product_name = item.get('productName', '').lower()
    meter_name = item.get('meterName', '').lower()
    return (
        'windows' not in product_name and
        'windows' not in meter_name and
        'cloud services' not in product_name and
        'cloud services' not in meter_name and
        'virtual machines' in product_name
    )

# def fetch_azure_pricing(sku='Standard_D8as_v5', region='GermanyWestCentral'):
def fetch_azure_pricing(sku:str, region:str):
    api_url = "https://prices.azure.com/api/retail/prices"
    query = f"armRegionName eq '{region}' and armSkuName eq '{sku}'"
    all_items = []

    response = requests.get(api_url, params={'$filter': query})
    try:
        json_data = json.loads(response.text)
    except json.JSONDecodeError:
        return {}, {}

    if 'Items' not in json_data:
        return {}, {}

    all_items.extend(json_data['Items'])
    next_page = json_data.get('NextPageLink')

    while next_page:
        response = requests.get(next_page)
        json_data = json.loads(response.text)
        if 'Items' in json_data:
            all_items.extend(json_data['Items'])
        next_page = json_data.get('NextPageLink')

    return parse_items(all_items)

def parse_items(items):
    pricing_map = {}
    labels_map = {}

    for item in items:
        if not is_linux_item(item):
            continue

        sku = item.get('armSkuName', '')
        region = item.get('armRegionName', '')
        model = determine_model(item)
        payment = extract_payment_option(item.get('skuName', '')) if model.startswith('Reserved') else '-'
        price = item.get('retailPrice', 0.0)
        term = item.get('reservationTerm', '-')

        label = f"{model}"
        if model.startswith('Reserved'):
            label += f" - {payment}"

        if label not in pricing_map:
            pricing_map[label] = round(price * HOURS_PER_MONTH, 2)
            labels_map[label] = {
                'raw_price': float(price),
                'term': term,
                'payment': payment,
                'sku': sku,
                'region': region  
            }

    return pricing_map, labels_map



