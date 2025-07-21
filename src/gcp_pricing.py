
from googleapiclient.discovery import build
from google.auth import default
from collections import defaultdict

def fetch_gcp_pricing(instance_type: str, region: str, cpu: int, ram: float):
    """
    Fetches GCP VM pricing data (On-Demand, Spot, and CUD) for a given instance type, region, CPU, and RAM configuration.

    Parameters:
    ----------
    instance_type : str
        The GCP instance family or type (e.g., 'n2-standard').
    region : str
        The GCP region (e.g., 'us-central1').
    cpu : int
        Number of vCPUs requested.
    ram : float
        Amount of memory in GB.

    Returns:
    -------
    Tuple[dict, dict]
        A tuple of two dictionaries:
        - gcp_data: Aggregated pricing data by pricing model (hourly, monthly, yearly).
        - gcp_labels: Metadata labels for display or logging, including term type and resource configuration.

    Notes:
    -----
    - This function requires Google Cloud credentials to be authenticated in the environment.
    - Uses Google Cloud Billing API to fetch SKU-level pricing information.
    - Filters SKUs based on instance family, region, and usage type.
    - Combines core and RAM pricing to produce total cost per pricing model.
    - Supports:
        - OnDemand
        - Preemptible (Spot)
        - Committed Use Discounts (1 year and 3 years)
    """

    ram_gb = round(ram, 2)
    cores = int(cpu)

    print(f"🔍 Instance: {instance_type}, Region: {region}, CPU: {cores}, RAM: {ram_gb} GB")

    credentials, _ = default()
    service = build('cloudbilling', 'v1', credentials=credentials)
    compute_service_id = 'services/6F81-5844-456A'
    request = service.services().skus().list(parent=compute_service_id)

    skus = []
    while request is not None:
        response = request.execute()
        skus.extend(response.get('skus', []))
        request = service.services().skus().list_next(previous_request=request, previous_response=response)

    print(f" Total SKUs fetched: {len(skus)}")

    results = {
        "OnDemand": {},
        "Spot": {},
        "CUD": {"Commit1Yr": {}, "Commit3Yr": {}}
    }

    family_prefix = instance_type.split("-")[0].upper()  # e.g. "N2", "N2D"
    cud_key_map = {
        "COMMIT1YR": "Commit1Yr",
        "COMMIT3YR": "Commit3Yr"
    }

    def is_exact_family(desc: str, family: str):
        desc = desc.upper()
        if family == "N2":
            return "N2" in desc and "N2D" not in desc
        elif family == "N2D":
            return "N2D" in desc
        return False

    def set_price(target, key, val, label, desc):
        if key not in target:
            target[key] = val
            print(f"{label}: {val} | {desc}")

    for sku in skus:
        desc = sku.get("description", "").upper()
        category = sku.get("category", {})
        pricing_info = sku.get("pricingInfo", [])
        usage_type = category.get("usageType", "").upper()
        regions = [r.lower() for r in sku.get("serviceRegions", [])]

        if "SOLE TENANCY" in desc or "CUSTOM" in desc:
            continue
        if not any(r in regions for r in [region.lower(), 'global']):
            continue
        if not pricing_info:
            continue
        if not is_exact_family(desc, family_prefix):
            continue

        try:
            tiered = pricing_info[0]['pricingExpression']['tieredRates'][0]['unitPrice']
            units = int(tiered.get('units', 0))
            nanos = tiered.get('nanos', 0) / 1e9
            price = units + nanos
        except (TypeError, ValueError, IndexError, KeyError):
            continue

        # OnDemand
        if usage_type == "ONDEMAND":
            if any(k in desc for k in ["CORE", "CPU", "VCPU"]):
                set_price(results["OnDemand"], "core", price, " OnDemand CORE", desc)
            elif "RAM" in desc:
                set_price(results["OnDemand"], "ram", price, " OnDemand RAM", desc)

        # Spot (Preemptible)
        elif usage_type == "PREEMPTIBLE":
            if any(k in desc for k in ["CORE", "CPU", "VCPU"]):
                set_price(results["Spot"], "core", price, "⚡ Spot CORE", desc)
            elif "RAM" in desc:
                set_price(results["Spot"], "ram", price, "⚡ Spot RAM", desc)

        # CUD
        elif usage_type in cud_key_map:
            cud_key = cud_key_map[usage_type]
            if any(k in desc for k in ["CORE", "CPU", "VCPU"]):
                set_price(results["CUD"][cud_key], "core", price, f"💳 CUD CORE ({cud_key})", desc)
            elif "RAM" in desc:
                set_price(results["CUD"][cud_key], "ram", price, f"💳 CUD RAM ({cud_key})", desc)

    def combined_price(core_price, ram_price, cores, ram_gb):
        hourly = cores * core_price + ram_gb * ram_price
        monthly = hourly * 730
        yearly = monthly * 12
        return {
            "hourly": round(hourly, 4),
            "monthly": round(monthly, 2),
            "yearly": round(yearly, 2)
        }

    gcp_data = {}
    gcp_labels = {}

    for term_key, pricing in {
        "GCP-OnDemand": results["OnDemand"],
        "GCP-Spot": results["Spot"],
        "GCP-Commit1Yr": results["CUD"]["Commit1Yr"],
        "GCP-Commit3Yr": results["CUD"]["Commit3Yr"]
    }.items():
        if "core" in pricing and "ram" in pricing:
            term = term_key.split("-")[-1]
            price = combined_price(pricing["core"], pricing["ram"], cores, ram_gb)
            gcp_data[term_key] = price
            gcp_labels[term_key] = {
                "term": term,
                "raw_price": price["hourly"],
                "payment": "Monthly" if "Commit" in term else "-",
                "instance_type": instance_type,
                "region": region,
                "cpu": cores,
                "memory": ram_gb
            }
            print(f"💡 {term_key}:", price)

    if not gcp_data:
        print("No pricing data found for this configuration.")

    return gcp_data, gcp_labels
