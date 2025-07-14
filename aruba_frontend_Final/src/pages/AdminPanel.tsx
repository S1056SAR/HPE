import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; // If you're using React Router
import { ArrowLeft } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
const REST_ENDPOINT = "/admin";

export default function AdminPanel() {
    const [log, setLog] = useState<string[]>([]);
    const [jsonPath, setJsonPath] = useState("");
    const [jsonVendor, setJsonVendor] = useState("");

    // Optional: Enable only if you're using React Router
    const navigate = useNavigate();

    const logMessage = (msg: string) =>
        setLog((prev) => [
            ...prev,
            `[${new Date().toLocaleTimeString()}] ${msg}`,
        ]);

    const trigger = async (endpoint: string, options: RequestInit = {}) => {
        logMessage(`Calling ${REST_ENDPOINT}${endpoint}...`);
        try {
            const res = await fetch(
                `${API_BASE_URL}${REST_ENDPOINT}${endpoint}`,
                {
                    method: "POST",
                    ...options,
                }
            );
            const data = await res.json();
            logMessage(data.message || "Success.");
        } catch (err) {
            logMessage(`Error on ${endpoint}: ${err}`);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white px-6 py-10">
            {/* Back Button */}
            <div className="mb-6 flex items-center">
                <Button
                    variant="secondary"
                    className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700"
                    onClick={() => navigate(-1)} // or replace with: window.history.back()
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </Button>
            </div>

            {/* Header */}
            <h1 className="text-3xl font-bold mb-6">🛠 Admin Control Panel</h1>

            {/* Admin Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Reset */}
                <Card>
                    <CardContent className="p-4">
                        <h2 className="text-xl font-semibold mb-2">
                            Full System Reset
                        </h2>
                        <p className="text-sm mb-4">
                            Resets vector DB, ingestion tracking, and update
                            checker state.
                        </p>
                        <Button
                            variant="destructive"
                            onClick={() => trigger("/reset")}
                        >
                            Reset All
                        </Button>
                    </CardContent>
                </Card>

                {/* Clear Cache */}
                <Card>
                    <CardContent className="p-4">
                        <h2 className="text-xl font-semibold mb-2">
                            Clear Scraper Cache
                        </h2>
                        <p className="text-sm mb-4">
                            Clears diskcache used by the scraper.
                        </p>
                        <Button onClick={() => trigger("/clear-cache")}>
                            Clear Cache
                        </Button>
                    </CardContent>
                </Card>

                {/* Warm Cache */}
                <Card>
                    <CardContent className="p-4">
                        <h2 className="text-xl font-semibold mb-2">
                            Warm Cache
                        </h2>
                        <p className="text-sm mb-4">
                            Preloads and caches known vendor URLs (Arista,
                            Aruba, Juniper).
                        </p>
                        <Button onClick={() => trigger("/warm-cache")}>
                            Start Cache Warming
                        </Button>
                    </CardContent>
                </Card>

                {/* Ingest JSON */}
                <Card>
                    <CardContent className="p-4 space-y-4">
                        <h2 className="text-xl font-semibold">Ingest JSON</h2>
                        <div>
                            <Label>JSON File Path</Label>
                            <Input
                                value={jsonPath}
                                onChange={(e) => setJsonPath(e.target.value)}
                                placeholder="./scraped_data.json"
                            />
                        </div>
                        <div>
                            <Label>Vendor</Label>
                            <Input
                                value={jsonVendor}
                                onChange={(e) => setJsonVendor(e.target.value)}
                                placeholder="Juniper"
                            />
                        </div>
                        <Button
                            onClick={() =>
                                trigger("/ingest-json", {
                                    headers: {
                                        "Content-Type": "application/json",
                                    },
                                    body: JSON.stringify({
                                        path: jsonPath,
                                        vendor: jsonVendor,
                                    }),
                                })
                            }
                        >
                            Ingest JSON
                        </Button>
                    </CardContent>
                </Card>

                {/* Start Update Checker */}
                <Card>
                    <CardContent className="p-4">
                        <h2 className="text-xl font-semibold mb-2">
                            Start Update Checker
                        </h2>
                        <p className="text-sm mb-4">
                            Starts the background update checker.
                        </p>
                        <Button
                            onClick={() => trigger("/start-update-checker")}
                        >
                            Start Update Checker
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {/* Logs */}
            <div className="mt-10">
                <h2 className="text-xl font-semibold mb-3">Logs</h2>
                <Textarea
                    value={log.join("\n")}
                    readOnly
                    className="bg-gray-900 text-green-400 h-60"
                />
            </div>
        </div>
    );
}
