"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchTarget } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function TargetPage() {
    const params = useParams();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function load() {
            try {
                const res = await fetchTarget(params.id as string);
                setData(res);
            } catch {
                setError("Failed to load target details");
            } finally {
                setLoading(false);
            }
        }
        if (params.id) load();
    }, [params.id]);

    if (loading) return <div className="p-8 text-center">Loading...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
    if (!data) return <div className="p-8 text-center">Target not found</div>;

    const { target, drugs, signatures } = data;

    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold">{target.symbol}</h1>
                    <p className="text-xl text-muted-foreground">{target.full_name}</p>
                </div>
                <Link href="/">
                    <Button variant="outline">Back to Search</Button>
                </Link>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Details</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                        <div><span className="font-semibold">Family:</span> {target.family}</div>
                        <div><span className="font-semibold">Class:</span> {target.class}</div>
                        <div><span className="font-semibold">UniProt:</span> {target.uniprot_id}</div>
                        <div><span className="font-semibold">Ensembl:</span> {target.ensembl_id}</div>
                    </CardContent>
                </Card>

                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle>Associated Drugs ({drugs.length})</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {drugs.length === 0 ? (
                            <p className="text-muted-foreground">No drugs found for this target.</p>
                        ) : (
                            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                                {drugs.map((d: any) => (
                                    <li key={d.drug_id} className="border p-3 rounded hover:bg-muted">
                                        <Link href={`/drug/${d.drug_id}`} className="block">
                                            <div className="font-medium text-primary">{d.epi_drugs.name}</div>
                                            <div className="text-sm text-muted-foreground">{d.mechanism_of_action}</div>
                                            {d.epi_drugs.fda_approved && (
                                                <span className="inline-block mt-1 text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">Approved</span>
                                            )}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>
            </div>

            {signatures.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle>Signatures & Complexes</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul>
                            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                            {signatures.map((s: any) => (
                                <li key={s.signature_id} className="mb-2">
                                    <span className="font-medium">{s.epi_signatures.name}</span>
                                    <span className="text-muted-foreground ml-2">({s.role})</span>
                                </li>
                            ))}
                        </ul>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
