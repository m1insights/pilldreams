"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { fetchDrugDetails } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DrugPage() {
    const params = useParams();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function load() {
            try {
                const res = await fetchDrugDetails(params.id as string);
                setData(res);
            } catch {
                setError("Failed to load drug details");
            } finally {
                setLoading(false);
            }
        }
        if (params.id) load();
    }, [params.id]);

    if (loading) return <div className="p-8 text-center">Loading...</div>;
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;
    if (!data) return <div className="p-8 text-center">Drug not found</div>;

    const { drug, targets, scores, chem_metrics } = data;

    // Find Total Score
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const totalScore = scores.find((s: any) => s.total_score > 0)?.total_score || 0;

    return (
        <div className="container mx-auto py-8 space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold flex items-center gap-4">
                        {drug.name}
                        {drug.fda_approved && (
                            <span className="text-sm bg-green-100 text-green-800 px-3 py-1 rounded-full font-normal">FDA Approved</span>
                        )}
                    </h1>
                    <p className="text-xl text-muted-foreground mt-2">Type: {drug.drug_type}</p>
                </div>
                <Link href="/">
                    <Button variant="outline">Back to Search</Button>
                </Link>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
                {/* Scores Card */}
                <Card className="bg-slate-50 border-slate-200">
                    <CardHeader>
                        <CardTitle>Epigenetic Score</CardTitle>
                    </CardHeader>
                    <CardContent className="text-center">
                        <div className="text-5xl font-bold text-primary mb-2">{totalScore.toFixed(1)}</div>
                        <p className="text-sm text-muted-foreground">Total Score (0-100)</p>

                        {chem_metrics && (
                            <div className="mt-6 grid grid-cols-2 gap-4 text-left text-sm">
                                <div>
                                    <div className="font-semibold">ChemScore</div>
                                    <div>{chem_metrics.chem_score}</div>
                                </div>
                                <div>
                                    <div className="font-semibold">Potency (pAct)</div>
                                    <div>{chem_metrics.p_act_best}</div>
                                </div>
                                <div>
                                    <div className="font-semibold">Selectivity</div>
                                    <div>{chem_metrics.delta_p?.toFixed(1) || "N/A"}</div>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Targets Card */}
                <Card className="md:col-span-2">
                    <CardHeader>
                        <CardTitle>Targets</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-3">
                            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                            {targets.map((t: any) => (
                                <li key={t.target_id} className="flex justify-between items-center border-b pb-2 last:border-0">
                                    <div>
                                        <Link href={`/target/${t.target_id}`} className="font-medium text-primary hover:underline">
                                            {t.epi_targets.symbol}
                                        </Link>
                                        <div className="text-xs text-muted-foreground">{t.epi_targets.family}</div>
                                    </div>
                                    <div className="text-sm">{t.mechanism_of_action}</div>
                                </li>
                            ))}
                        </ul>
                    </CardContent>
                </Card>
            </div>

            {/* Indications & Scores */}
            <Card>
                <CardHeader>
                    <CardTitle>Indications & Scores</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                                <tr>
                                    <th className="px-4 py-3">Indication</th>
                                    <th className="px-4 py-3">BioScore</th>
                                    <th className="px-4 py-3">Tractability</th>
                                    <th className="px-4 py-3">Total Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                                {scores.map((s: any) => (
                                    <tr key={s.id} className="border-b hover:bg-gray-50">
                                        <td className="px-4 py-3 font-medium">
                                            <Link href={`/indication/${s.indication_id}`} className="hover:underline">
                                                {s.epi_indications.name}
                                            </Link>
                                        </td>
                                        <td className="px-4 py-3">{s.bio_score?.toFixed(1)}</td>
                                        <td className="px-4 py-3">{s.tractability_score}</td>
                                        <td className="px-4 py-3 font-bold">{s.total_score?.toFixed(1)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
