import requests

def fetch_pubmed_count(drug_name: str) -> int:
    """Fetch PubMed article count for a drug."""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": f"{drug_name}[Title/Abstract]",
        "retmode": "json"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return int(data["esearchresult"]["count"])
    except Exception as e:
        print(f"Error fetching PubMed count for {drug_name}: {e}")
        return 0

def fetch_openfda_stats(drug_name: str) -> dict:
    """Fetch OpenFDA adverse event stats."""
    url = "https://api.fda.gov/drug/event.json"
    # Count total reports
    params = {
        "search": f"patient.drug.medicinalproduct:{drug_name}",
        "limit": 1
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 404:
             return {"count": 0, "serious_ae_ratio": 0.0}
        response.raise_for_status()
        
        data = response.json()
        total_count = data["meta"]["results"]["total"]
        
        # Count serious reports
        params["search"] += " AND serious:1"
        response_serious = requests.get(url, params=params)
        if response_serious.status_code == 404:
             serious_count = 0
        else:
             data_serious = response_serious.json()
             serious_count = data_serious["meta"]["results"]["total"]
        
        serious_ratio = serious_count / total_count if total_count > 0 else 0.0
        
        return {
            "count": total_count,
            "serious_ae_ratio": serious_ratio
        }
    except Exception as e:
        print(f"Error fetching OpenFDA stats for {drug_name}: {e}")
        return {"count": 0, "serious_ae_ratio": 0.0}
