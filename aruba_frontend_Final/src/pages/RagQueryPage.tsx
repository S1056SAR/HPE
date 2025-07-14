import { useState } from "react";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { FileText, Search, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import { MarkdownRenderer } from "@/components/MarkdownRenderer";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const RagQueryPage = () => {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleSearch = async () => {
        if (!query.trim()) {
            alert("Please enter a query.");
            return;
        }

        setIsLoading(true);
        setResults([]);

        try {
            const response = await fetch(`${API_BASE_URL}/query_rag`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ query: query }),
            });

            const data = await response.json();
            console.log(`Raw Server Data:`, data);

            if (response.ok) {
                const formatted = [
                    {
                        id: 1,
                        title: "LLM Generated Answer",
                        excerpt: data.response,
                        isAnalysis: false,
                        isCode: true, // flag for markdown rendering
                    },
                    {
                        id: 2,
                        title: "Query Analysis",
                        analysis: data.analysis,
                        isAnalysis: true, // flag to render in key-value table
                    },
                ];

                // const formatted = [
                //     {
                //         id: 1,
                //         title: "LLM Generated Answer",
                //         excerpt: data.response,
                //     },
                //     ...(data.analysis
                //         ? [
                //               {
                //                   id: 2,
                //                   title: "Query Analysis",
                //                   excerpt: `Intent: ${data.analysis.intent}\nVendor: ${data.analysis.source}\nOriginal Query: ${data.analysis.original_query}`,
                //               },
                //           ]
                //         : []),
                // ];
                setIsLoading(false);
                // setResults(data.response);
                setResults(formatted);
                console.log(`Formatted: ${formatted}`);
            } else {
                // throw new Error("Failed to fetch response from RAG");
                setResults([
                    {
                        id: 1,
                        title: "Error",
                        excerpt: data.detail || "Unexpected error.",
                    },
                ]);
            }
        } catch (error) {
            console.error("Fetch error:", error);
            setResults([
                {
                    id: 1,
                    title: "Error",
                    excerpt: "Failed to reach server. Please try again.",
                },
            ]);
        } finally {
            setIsLoading(false);
        }

        // // TODO: Replace with actual API call
        // console.log("Searching documentation for:", query);
        // console.log(
        //     "API Endpoint: // Insert API URL for documentation queries here"
        // );

        // // Simulate API call
        // setTimeout(() => {
        //     setIsLoading(false);
        //     setResults([
        //         {
        //             id: 1,
        //             title: "Network Configuration Guide",
        //             excerpt: "Complete guide for configuring Aruba networks...",
        //         },
        //         {
        //             id: 2,
        //             title: "API Documentation",
        //             excerpt: "REST API endpoints and usage examples...",
        //         },
        //     ]);
        // }, 2000);
    };

    return (
        <div className="min-h-screen bg-black">
            <Header />

            <main className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link to="/">
                        <Button
                            variant="outline"
                            className="bg-transparent border-gray-700 text-white hover:border-neon-blue"
                        >
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back
                        </Button>
                    </Link>
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-black/50 border-neon-blue text-neon-blue border">
                            <FileText className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold neon-text">
                                Agentic-RAG Search
                            </h1>
                            <p className="text-gray-400">
                                Powered by Agentic-RAG Technique
                                (Retrieval-Augmented-Generation)
                            </p>
                        </div>
                    </div>
                </div>

                {/* Search Interface */}
                <Card className="glass-morphism mb-8">
                    <CardHeader>
                        <CardTitle className="text-neon-blue">Search</CardTitle>
                        <CardDescription>
                            Enter your Agentic-RAG query
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex gap-4">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Enter your search query..."
                                className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-blue focus:outline-none"
                            />
                            <Button
                                onClick={handleSearch}
                                disabled={isLoading || !query.trim()}
                                className="bg-neon-blue text-black hover:bg-neon-cyan"
                            >
                                {isLoading ? (
                                    <div className="flex items-center space-x-2">
                                        <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                                        <span>Searching...</span>
                                    </div>
                                ) : (
                                    <>
                                        <Search className="w-4 h-4 mr-2" />
                                        Search
                                    </>
                                )}
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Results */}
                {results.length > 0 && (
                    <div className="space-y-4">
                        <h2 className="text-xl font-bold text-neon-blue">
                            Agentic-RAG Output
                        </h2>
                        {results.map((result) => (
                            <Card
                                key={result.id}
                                className="glass-morphism hover:border-neon-blue transition-colors"
                            >
                                <CardContent className="p-6">
                                    <h3 className="text-lg font-semibold text-white mb-2">
                                        {result.title}
                                    </h3>
                                    {/* <p className="text-gray-400">
                                        {result.excerpt}
                                    </p> */}
                                    {result.isAnalysis ? (
                                        <div className="text-gray-300 text-sm space-y-1">
                                            {Object.entries(
                                                result.analysis
                                            ).map(([key, value]) => (
                                                <div key={key}>
                                                    <span className="font-semibold capitalize">
                                                        {key}:
                                                    </span>{" "}
                                                    {String(value)}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <details className="bg-black/30 border border-gray-600 rounded-lg px-4 py-2 cursor-pointer">
                                            <summary className="text-neon-blue font-medium mb-2">
                                                View Full Answer
                                            </summary>
                                            <MarkdownRenderer
                                                content={result.excerpt}
                                            />
                                        </details>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {/* API Integration Info */}
                <Card className="glass-morphism mt-8">
                    <CardHeader>
                        <CardTitle className="text-neon-orange">
                            🔧 API Integration
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2 text-sm text-gray-300">
                            <p>
                                • <strong>Endpoint:</strong>{" "}
                                <code className="bg-gray-800 px-2 py-1 rounded">
                                    {API_BASE_URL}/query_rag
                                </code>
                            </p>
                            <p>
                                • <strong>Method:</strong> POST
                            </p>
                            <p>
                                • <strong>Headers:</strong> Authorization,
                                Content-Type
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </main>
        </div>
    );
};

export default RagQueryPage;
