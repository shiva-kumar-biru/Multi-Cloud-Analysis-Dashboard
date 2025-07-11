##################################. STATIC CODE  ########################################

from googleapiclient.discovery import build
from google.auth import default
from collections import defaultdict

def fetch_gcp_pricing(instance_type="n2-standard-4", region="us-east4"):
    credentials, _ = default()
    service = build('cloudbilling', 'v1', credentials=credentials)

    compute_service_id = 'services/6F81-5844-456A'
    request = service.services().skus().list(parent=compute_service_id) #lists all available SKUs under Compute Engine. GET https://cloudbilling.googleapis.com/v1/services/SERVICE_ID/skus?key=<var>API_KEY</var>
    skus = []
    while request is not None:
        response = request.execute()
        skus.extend(response.get('skus', []))
        request = service.services().skus().list_next(previous_request=request, previous_response=response)

    results = {
        "OnDemand": defaultdict(float),
        "Spot": defaultdict(float),
        "CUD": {"Commit1Yr": {}, "Commit3Yr": {}}
    }

    prefix = instance_type.split("-")[0].upper()

    for sku in skus:
        desc = sku.get("description", "")
        category = sku.get("category", {})
        pricing_info = sku.get("pricingInfo", [])
        usage_type = category.get("usageType", "")
        regions = sku.get("serviceRegions", [])

        if prefix not in desc.upper():
            continue

        # Dynamically match only the selected region (or include 'global' SKUs if desired)
        if not any(r in regions for r in [region, 'global']):
            continue

        if not pricing_info:
            continue


        tiered = pricing_info[0]['pricingExpression']['tieredRates'][0]['unitPrice']
        try:
            units = int(tiered.get('units', 0))
            nanos = tiered.get('nanos', 0) / 1e9
            price = units + nanos
        except (TypeError, ValueError):
            continue

        if usage_type == "OnDemand" and "N2 Instance" in desc and "Sole Tenancy" not in desc and "Custom" not in desc:
            if "Core" in desc:
                results["OnDemand"]["core"] = price
            elif "Ram" in desc:
                results["OnDemand"]["ram"] = price
        elif usage_type == "Preemptible" and "N2 Instance" in desc and "Custom" not in desc:
            if "Core" in desc:
                results["Spot"]["core"] = price
            elif "Ram" in desc:
                results["Spot"]["ram"] = price
        elif usage_type in ["Commit1Yr", "Commit3Yr"] and "N2" in desc and ("Cpu" in desc or "Ram" in desc):
            term = usage_type
            if "Cpu" in desc:
                results["CUD"][term]["core"] = price
            elif "Ram" in desc:
                results["CUD"][term]["ram"] = price

    def combined_price(core_price, ram_price, cores=4, ram_gb=16):
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

    if "core" in results["OnDemand"] and "ram" in results["OnDemand"]:
        price = combined_price(results["OnDemand"]["core"], results["OnDemand"]["ram"])
        gcp_data["GCP-OnDemand"] = price
        gcp_labels["GCP-OnDemand"] = {"term": "OnDemand", "raw_price": price["hourly"], "payment": "-", "instance_type": instance_type,
                "region": region}

    if "core" in results["Spot"] and "ram" in results["Spot"]:
        price = combined_price(results["Spot"]["core"], results["Spot"]["ram"])
        gcp_data["GCP-Spot"] = price
        gcp_labels["GCP-Spot"] = {"term": "Spot", "raw_price": price["hourly"], "payment": "-","instance_type": instance_type,
                "region": region}

    for term in ["Commit1Yr", "Commit3Yr"]:
        if "core" in results["CUD"][term] and "ram" in results["CUD"][term]:
            price = combined_price(results["CUD"][term]["core"], results["CUD"][term]["ram"])
            gcp_data[f"GCP-{term}"] = price
            gcp_labels[f"GCP-{term}"] = {"term": term, "raw_price": price["hourly"], "payment": "Monthly","instance_type": instance_type,
                       "region": region}

    return gcp_data, gcp_labels




#########################. DYNAMIC CODE #################################

from googleapiclient.discovery import build
from google.auth import default
from collections import defaultdict

def fetch_gcp_pricing(instance_type: str, region: str, cpu: int, ram: float):
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

    print(f"✅ Total SKUs fetched: {len(skus)}")

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
