const API_BASE_URL = "http://localhost:8000";

export async function fetchTargets() {
    const res = await fetch(`${API_BASE_URL}/epi/targets`);
    if (!res.ok) throw new Error("Failed to fetch targets");
    return res.json();
}

export async function fetchDrugs(params?: { target_id?: string; indication_id?: string; approved_only?: boolean }) {
    const url = new URL(`${API_BASE_URL}/epi/drugs`);
    if (params) {
        if (params.target_id) url.searchParams.append("target_id", params.target_id);
        if (params.indication_id) url.searchParams.append("indication_id", params.indication_id);
        if (params.approved_only) url.searchParams.append("approved_only", "true");
    }
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error("Failed to fetch drugs");
    return res.json();
}

export async function fetchDrugDetails(drugId: string) {
    const res = await fetch(`${API_BASE_URL}/epi/drugs/${drugId}`);
    if (!res.ok) throw new Error("Failed to fetch drug details");
    return res.json();
}

export async function fetchSignature(name: string) {
    const res = await fetch(`${API_BASE_URL}/epi/signatures/${name}`);
    if (!res.ok) throw new Error("Failed to fetch signature");
    return res.json();
}

export async function fetchTarget(id: string) {
    const res = await fetch(`${API_BASE_URL}/epi/targets/${id}`);
    if (!res.ok) throw new Error("Failed to fetch target");
    return res.json();
}

export async function fetchIndication(id: string) {
    const res = await fetch(`${API_BASE_URL}/epi/indications/${id}`);
    if (!res.ok) throw new Error("Failed to fetch indication");
    return res.json();
}

export async function searchEntities(query: string) {
    const res = await fetch(`${API_BASE_URL}/epi/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error("Failed to search");
    return res.json();
}
