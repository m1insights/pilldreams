"use client";

import { useState, useEffect, useCallback } from "react";
import { fetchTargets, fetchDrugs, searchEntities, companiesApi } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export function Search() {
    const [query, setQuery] = useState("");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [targets, setTargets] = useState<any[]>([]);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [drugs, setDrugs] = useState<any[]>([]);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [indications, setIndications] = useState<any[]>([]);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [companies, setCompanies] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [hasSearched, setHasSearched] = useState(false);

    const loadInitial = useCallback(async () => {
        try {
            const t = await fetchTargets();
            setTargets(t.slice(0, 8)); // Show top 8
            const d = await fetchDrugs({ approved_only: true });
            setDrugs(d.slice(0, 8));
            setIndications([]);
            // Load top companies
            try {
                const c = await companiesApi.list();
                setCompanies(c.slice(0, 6));
            } catch {
                setCompanies([]);
            }
            setHasSearched(false);
        } catch (e) {
            console.error(e);
        }
    }, []);

    useEffect(() => {
        loadInitial();
    }, [loadInitial]);

    const handleSearch = async () => {
        if (query.trim().length < 2) {
            loadInitial();
            return;
        }

        setLoading(true);
        try {
            const results = await searchEntities(query);
            setTargets(results.targets || []);
            setDrugs(results.drugs || []);
            setIndications(results.indications || []);
            setCompanies(results.companies || []);
            setHasSearched(true);
        } catch (e) {
            console.error("Search failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") {
            handleSearch();
        }
    };

    const clearSearch = () => {
        setQuery("");
        loadInitial();
    };

    return (
        <div id="search" className="w-full max-w-5xl mx-auto p-6 space-y-8">
            <div className="flex gap-4">
                <Input
                    placeholder="Search targets, drugs, indications..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 bg-neutral-900 border-neutral-700 text-white placeholder:text-neutral-500"
                />
                <Button onClick={handleSearch} disabled={loading} className="bg-white text-black hover:bg-neutral-200">
                    {loading ? "Searching..." : "Search"}
                </Button>
                {hasSearched && (
                    <Button onClick={clearSearch} variant="outline" className="border-neutral-700 text-neutral-300 hover:bg-neutral-800">
                        Clear
                    </Button>
                )}
            </div>

            {hasSearched && targets.length === 0 && drugs.length === 0 && indications.length === 0 && companies.length === 0 && (
                <div className="text-center py-8 text-neutral-400">
                    No results found for &quot;{query}&quot;
                </div>
            )}

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <Card className="bg-neutral-900 border-neutral-800">
                    <CardHeader>
                        <CardTitle className="text-white text-lg">
                            {hasSearched ? `Targets (${targets.length})` : "Top Epigenetic Targets"}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {targets.length === 0 ? (
                            <p className="text-neutral-500 text-sm">No targets found</p>
                        ) : (
                            <ul className="space-y-2">
                                {targets.map((t) => (
                                    <li key={t.id} className="flex justify-between items-center p-2 hover:bg-neutral-800 rounded">
                                        <Link href={`/target/${t.id}`} className="font-medium text-blue-400 hover:underline">
                                            {t.symbol}
                                        </Link>
                                        <span className="text-xs text-neutral-500 bg-neutral-800 px-2 py-1 rounded">{t.family}</span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>

                <Card className="bg-neutral-900 border-neutral-800">
                    <CardHeader>
                        <CardTitle className="text-white text-lg">
                            {hasSearched ? `Drugs (${drugs.length})` : "Approved Epigenetic Drugs"}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {drugs.length === 0 ? (
                            <p className="text-neutral-500 text-sm">No drugs found</p>
                        ) : (
                            <ul className="space-y-2">
                                {drugs.map((d) => (
                                    <li key={d.id} className="flex justify-between items-center p-2 hover:bg-neutral-800 rounded">
                                        <Link href={`/drug/${d.id}`} className="font-medium text-blue-400 hover:underline">
                                            {d.name}
                                        </Link>
                                        {d.fda_approved ? (
                                            <span className="text-xs bg-green-900 text-green-300 px-2 py-1 rounded-full">Approved</span>
                                        ) : (
                                            <span className="text-xs bg-yellow-900 text-yellow-300 px-2 py-1 rounded-full">Pipeline</span>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>

                {(hasSearched || indications.length > 0) && (
                    <Card className="bg-neutral-900 border-neutral-800">
                        <CardHeader>
                            <CardTitle className="text-white text-lg">
                                Indications ({indications.length})
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {indications.length === 0 ? (
                                <p className="text-neutral-500 text-sm">No indications found</p>
                            ) : (
                                <ul className="space-y-2">
                                    {indications.map((i) => (
                                        <li key={i.id} className="flex justify-between items-center p-2 hover:bg-neutral-800 rounded">
                                            <Link href={`/indication/${i.id}`} className="font-medium text-blue-400 hover:underline text-sm">
                                                {i.name}
                                            </Link>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </CardContent>
                    </Card>
                )}

                {(companies.length > 0 || hasSearched) && (
                    <Card className="bg-neutral-900 border-neutral-800">
                        <CardHeader>
                            <CardTitle className="text-white text-lg">
                                {hasSearched ? `Companies (${companies.length})` : "Epigenetics Companies"}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {companies.length === 0 ? (
                                <p className="text-neutral-500 text-sm">No companies found</p>
                            ) : (
                                <ul className="space-y-2">
                                    {companies.map((c) => (
                                        <li key={c.id} className="flex justify-between items-center p-2 hover:bg-neutral-800 rounded">
                                            <Link href={`/company/${c.id}`} className="font-medium text-blue-400 hover:underline">
                                                {c.name}
                                            </Link>
                                            {c.ticker ? (
                                                <span className="text-xs font-mono bg-purple-900/50 text-purple-300 px-2 py-1 rounded">{c.ticker}</span>
                                            ) : (
                                                <span className="text-xs bg-neutral-800 text-neutral-400 px-2 py-1 rounded">Private</span>
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
