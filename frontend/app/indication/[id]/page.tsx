"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchIndication } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function IndicationPage() {
    const params = useParams();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function load() {
            try {
                const res = await fetchIndication(params.id as string);
                setData(res);
            } catch {
                setError("Failed to load indication details");
            } finally {
                setLoading(false);
            }
        }
        if (params.id) load();
    }, [params.id]);

    if (loading) return <div className="p-8 text-center">Loading...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
    if (!data) return <div className="p-8 text-center">Indication not found</div>;

    const { indication, drugs } = data;

    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold">{indication.name}</h1>
                    <p className="text-xl text-muted-foreground">Disease Area: {indication.disease_area || "Oncology"}</p>
                </div>
                <Link href="/">
                    <Button variant="outline">Back to Search</Button>
                </Link>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Drugs for {indication.name} ({drugs.length})</CardTitle>
                </CardHeader>
                <CardContent>
                    {drugs.length === 0 ? (
                        <p className="text-muted-foreground">No drugs found for this indication.</p>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                            {drugs.map((d: any) => (
                                <Link key={d.drug_id} href={`/drug/${d.drug_id}`}>
                                    <div className="border p-4 rounded-lg hover:bg-muted transition-colors h-full">
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="font-bold text-lg text-primary">{d.epi_drugs.name}</div>
                                            {d.epi_drugs.fda_approved && (
                                                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Approved</span>
                                            )}
                                        </div>
                                        <div className="text-sm text-muted-foreground">
                                            <div>Status: <span className="capitalize">{d.approval_status}</span></div>
                                            {d.max_phase && <div>Phase: {d.max_phase}</div>}
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
