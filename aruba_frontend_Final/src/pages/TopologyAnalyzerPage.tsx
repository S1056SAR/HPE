import { useState, useRef } from "react";
import mermaid from "mermaid";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import { ArrowLeft, Network } from "lucide-react";
import { Link } from "react-router-dom";

import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
} from "@/components/ui/accordion";
import { MermaidViewer } from "@/components/MermaidViewer";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const TopologyAnalyzer = () => {
    const [image, setImage] = useState<File | null>(null);
    const [query, setQuery] = useState("");
    const [result, setResult] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(false);
    const filePreviewRef = useRef<HTMLDivElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith("image/")) {
            alert("Please upload a valid image file.");
            return;
        }

        setImage(file);

        const reader = new FileReader();
        reader.onload = (e) => {
            if (filePreviewRef.current) {
                filePreviewRef.current.innerHTML = `
                    <img src="${e.target?.result}" alt="Preview" class="max-h-40 rounded" />
                    <p class="text-sm text-gray-300 mt-2">${file.name}</p>
                `;
            }
        };
        reader.readAsDataURL(file);
    };

    const handleSubmit = async () => {
        if (!image || query.trim().length < 20) {
            alert("Upload an image and enter at least 20 characters of query.");
            return;
        }

        const formData = new FormData();
        formData.append("image", image);
        formData.append("replacement_query", query);

        setIsLoading(true);
        setResult(null);

        try {
            const res = await fetch(
                `${API_BASE_URL}/topology/analyze-topology`,
                {
                    method: "POST",
                    body: formData,
                }
            );

            const data = await res.json();
            console.log("Raw Server Response (Full Topology Analysis):", data); // <--- log here

            setResult(data);
            setTimeout(() => mermaid.run(), 100); // allow DOM to render
        } catch (err) {
            console.error("Analysis error:", err);
            alert("Failed to analyze topology.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white">
            <Header />

            <main className="container mx-auto px-4 py-8">
                {/* Header with Back Button & Icon */}
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
                            <Network className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold neon-text">
                                AI Network Topology Analyzer
                            </h1>
                            <p className="text-gray-400">
                                Upload a topology image & describe replacement
                                goals
                            </p>
                        </div>
                    </div>
                </div>

                {/* Upload + Query Form */}
                <Card className="glass-morphism mb-8">
                    <CardHeader>
                        <CardTitle className="text-neon-blue">
                            Upload & Query
                        </CardTitle>
                        <CardDescription>
                            Input the topology and your query
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <input
                            type="file"
                            accept="image/*"
                            onChange={handleFileChange}
                            className="mb-4"
                        />
                        <div ref={filePreviewRef} className="mb-4"></div>
                        <textarea
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            rows={6}
                            placeholder="Describe your network transformation goals..."
                            className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-blue focus:outline-none mb-4"
                        ></textarea>
                        <Button
                            onClick={handleSubmit}
                            disabled={isLoading}
                            className="bg-neon-blue text-black hover:bg-neon-cyan"
                        >
                            {isLoading ? "Analyzing..." : "Analyze Topology"}
                        </Button>
                    </CardContent>
                </Card>

                {/* Analysis Results */}
                {result && result.success && (
                    <Card className="glass-morphism">
                        <CardContent className="space-y-4">
                            <Accordion
                                type="multiple"
                                className="w-full text-white"
                            >
                                <AccordionItem value="summary">
                                    <AccordionTrigger className="text-neon-blue">
                                        Executive Summary & Analysis
                                    </AccordionTrigger>
                                    <AccordionContent className="space-y-3">
                                        <p className="text-white">
                                            {result.analysis_summary}
                                        </p>

                                        <div className="border-t border-gray-700 pt-4">
                                            <h3 className="text-lg font-semibold text-neon-cyan mb-2">
                                                AI Analysis & Justification
                                            </h3>
                                            <div
                                                // className="prose prose-invert max-w-none"
                                                className="text-white space-y-4 [&_h3]:text-lg [&_h3]:font-bold [&_p]:mb-3"
                                                dangerouslySetInnerHTML={{
                                                    __html: result.context_sources,
                                                }}
                                            />
                                        </div>

                                        <div className="border-t border-gray-700 pt-4 space-y-1">
                                            <p>
                                                {" "}
                                                <strong>
                                                    Total Replacements:
                                                </strong>{" "}
                                                {result.modification_details
                                                    ?.total_replacements ??
                                                    "Not specified"}
                                            </p>
                                            <p>
                                                {" "}
                                                <strong>
                                                    Implementation Phases:
                                                </strong>{" "}
                                                {result.implementation_guidance
                                                    ?.phases?.length > 0
                                                    ? `${result.implementation_guidance.phases.length} phases`
                                                    : "TBD"}
                                            </p>
                                            <p>
                                                <strong>Risk Level:</strong>{" "}
                                                Medium
                                            </p>
                                            <p>
                                                {" "}
                                                <strong>
                                                    Cost Category:
                                                </strong>{" "}
                                                Not specified
                                            </p>
                                        </div>
                                    </AccordionContent>
                                </AccordionItem>

                                <AccordionItem value="explanation">
                                    <AccordionTrigger className="text-neon-blue">
                                        Topology Explanation
                                    </AccordionTrigger>
                                    <AccordionContent className="text-white space-y-4 [&_h3]:text-lg [&_h3]:font-bold [&_p]:mb-3">
                                        {result.topology_explanation}
                                    </AccordionContent>
                                </AccordionItem>

                                <AccordionItem value="rag">
                                    <AccordionTrigger className="text-neon-blue">
                                        Agentic-RAG Justification
                                    </AccordionTrigger>

                                    <AccordionContent>
                                        <MarkdownRenderer
                                            content={result.context_sources}
                                        />
                                    </AccordionContent>
                                </AccordionItem>

                                <AccordionItem value="diagrams">
                                    <AccordionTrigger className="text-neon-blue">
                                        Topology Diagrams
                                    </AccordionTrigger>
                                    <AccordionContent className="text-white space-y-4 [&_h3]:text-lg [&_h3]:font-bold [&_p]:mb-3">
                                        <MermaidViewer
                                            code={result.diagrams?.original}
                                            title="Original Topology"
                                        />
                                        <MermaidViewer
                                            code={result.diagrams?.modified}
                                            title="Proposed Topology"
                                            pngUrl={
                                                result.diagrams
                                                    ?.proposed_png_url
                                            }
                                            svgUrl={
                                                result.diagrams
                                                    ?.proposed_svg_url
                                            }
                                        />
                                        {/* <MermaidViewer
                                            code={result.diagrams?.comparison}
                                            title="Comparison View"
                                        /> */}
                                        {/* <pre className="bg-gray-900 p-4 rounded mb-4">
                                            {result.diagrams?.original}
                                        </pre>
                                        <pre className="bg-gray-900 p-4 rounded mb-4">
                                            {result.diagrams?.modified}
                                        </pre> */}
                                        {/* <pre className="bg-gray-900 p-4 rounded">
                                            {result.diagrams?.comparison}
                                        </pre> */}
                                    </AccordionContent>
                                </AccordionItem>

                                <AccordionItem value="modifications">
                                    <AccordionTrigger className="text-neon-blue">
                                        Modification Details
                                    </AccordionTrigger>
                                    <AccordionContent>
                                        <p>
                                            Total Replacements:{" "}
                                            {
                                                result.modification_details
                                                    ?.total_replacements
                                            }
                                        </p>
                                    </AccordionContent>
                                </AccordionItem>

                                <AccordionItem value="proposed-infrastructure">
                                    <AccordionTrigger className="text-neon-blue">
                                        Proposed Infra with Replacements
                                    </AccordionTrigger>
                                    <AccordionContent
                                        // className="text-white space-y-3"
                                        className="bg-black/30 p-4 rounded-lg text-white space-y-4 [&_h3]:text-lg [&_h3]:font-bold [&_p]:mb-3"
                                    >
                                        <p>
                                            <strong>Total Devices:</strong>{" "}
                                            {result.modified_topology?.devices
                                                ?.length ?? "Unknown"}
                                        </p>

                                        {result.modified_topology?.devices
                                            ?.length > 0 ? (
                                            <ul className="list-disc list-inside space-y-2">
                                                {result.modified_topology.devices.map(
                                                    (device, index) => {
                                                        const isReplaced =
                                                            !!device.notes;
                                                        return (
                                                            <li key={index}>
                                                                {isReplaced}
                                                                <strong>
                                                                    {device.id}
                                                                </strong>
                                                                :{" "}
                                                                {device.vendor ||
                                                                    "Unknown"}{" "}
                                                                {device.model ||
                                                                    "Unknown"}
                                                                {isReplaced && (
                                                                    <em className="block text-sm text-gray-400 ml-6">
                                                                        {
                                                                            device.notes
                                                                        }
                                                                    </em>
                                                                )}
                                                            </li>
                                                        );
                                                    }
                                                )}
                                            </ul>
                                        ) : (
                                            <p>
                                                No devices listed in modified
                                                topology.
                                            </p>
                                        )}
                                    </AccordionContent>
                                </AccordionItem>

                                <AccordionItem value="modification-impact">
                                    <AccordionTrigger className="text-neon-blue">
                                        Topology Modification Impact
                                    </AccordionTrigger>
                                    <AccordionContent className="text-white space-y-3">
                                        <p>
                                            <strong>Performance Impact:</strong>{" "}
                                            {
                                                result.recommendations
                                                    ?.topology_modifications
                                                    ?.performance_impact
                                            }
                                        </p>
                                        <p>
                                            <strong>
                                                Security Enhancements:
                                            </strong>{" "}
                                            {
                                                result.recommendations
                                                    ?.topology_modifications
                                                    ?.security_enhancements
                                            }
                                        </p>
                                        <p>
                                            <strong>Structural Changes:</strong>{" "}
                                            {
                                                result.recommendations
                                                    ?.topology_modifications
                                                    ?.structural_changes
                                            }
                                        </p>
                                    </AccordionContent>
                                </AccordionItem>

                                {/* <AccordionItem value="cost-analysis">
                                    <AccordionTrigger className="text-neon-blue">
                                        Cost Analysis
                                    </AccordionTrigger>
                                    <AccordionContent className="text-white space-y-3">
                                        <p>
                                            <strong>Hardware Costs:</strong>{" "}
                                            {
                                                result.recommendations
                                                    ?.cost_analysis
                                                    ?.hardware_costs
                                            }
                                        </p>
                                        <p>
                                            <strong>
                                                Implementation Costs:
                                            </strong>{" "}
                                            {
                                                result.recommendations
                                                    ?.cost_analysis
                                                    ?.implementation_costs
                                            }
                                        </p>
                                        <p>
                                            <strong>
                                                Operational Savings:
                                            </strong>{" "}
                                            {
                                                result.recommendations
                                                    ?.cost_analysis
                                                    ?.operational_savings
                                            }
                                        </p>
                                        <p>
                                            <strong>Total Project Cost:</strong>{" "}
                                            {
                                                result.recommendations
                                                    ?.cost_analysis
                                                    ?.total_project_cost
                                            }
                                        </p>
                                    </AccordionContent>
                                </AccordionItem> */}

                                <AccordionItem value="impl">
                                    <AccordionTrigger className="text-neon-blue">
                                        Implementation Guidance
                                    </AccordionTrigger>
                                    <AccordionContent>
                                        <p>
                                            {result.implementation_guidance
                                                ?.phases?.length > 0
                                                ? "Phases included"
                                                : "No phases provided."}
                                        </p>
                                    </AccordionContent>
                                </AccordionItem>

                                <AccordionItem value="replacements">
                                    <AccordionTrigger className="text-neon-blue">
                                        Detailed Device Replacement
                                        Recommendations
                                    </AccordionTrigger>
                                    <AccordionContent
                                        // className="space-y-6"
                                        className="text-white space-y-4 [&_h3]:text-lg [&_h3]:font-bold [&_p]:mb-3"
                                    >
                                        {result.recommendations?.replacements?.map(
                                            (replacement, index) => (
                                                <div
                                                    key={index}
                                                    className="border border-gray-700 p-4 rounded-lg bg-black/40"
                                                >
                                                    <h3 className="text-lg font-semibold text-neon-blue mb-2">
                                                        Replacement {index + 1}
                                                    </h3>
                                                    <p>
                                                        <strong>
                                                            Original Device:
                                                        </strong>{" "}
                                                        {`${replacement.original_device?.vendor} ${replacement.original_device?.model}`}
                                                    </p>
                                                    <p>
                                                        <strong>
                                                            Recommended Device:
                                                        </strong>{" "}
                                                        {`${replacement.recommended_device?.vendor} ${replacement.recommended_device?.model}`}
                                                    </p>
                                                    <p>
                                                        <strong>
                                                            Features:
                                                        </strong>{" "}
                                                        {replacement.recommended_device?.features?.join(
                                                            ", "
                                                        ) || "N/A"}
                                                    </p>
                                                    <p>
                                                        <strong>
                                                            Justification:
                                                        </strong>{" "}
                                                        {replacement
                                                            .recommended_device
                                                            ?.justification ||
                                                            "N/A"}
                                                    </p>
                                                    <p>
                                                        <strong>
                                                            Cost/Benefit:
                                                        </strong>{" "}
                                                        {replacement
                                                            .recommended_device
                                                            ?.cost_benefit ||
                                                            "N/A"}
                                                    </p>
                                                </div>
                                            )
                                        )}
                                    </AccordionContent>
                                </AccordionItem>
                            </Accordion>

                            {/* Download Button */}
                            <Button
                                onClick={() => {
                                    const blob = new Blob(
                                        [JSON.stringify(result, null, 2)],
                                        {
                                            type: "application/json",
                                        }
                                    );
                                    const url = URL.createObjectURL(blob);
                                    const a = document.createElement("a");
                                    a.href = url;
                                    a.download =
                                        "topology-analysis-report.json";
                                    a.click();
                                    URL.revokeObjectURL(url);
                                }}
                                className="mt-6 bg-neon-cyan text-black hover:bg-neon-blue"
                            >
                                Download Full Report
                            </Button>
                        </CardContent>
                    </Card>
                )}

                {result && result.error && (
                    <p className="text-red-500 mt-4">{result.error}</p>
                )}

                {/* API Integration Info */}
                <Card className="glass-morphism mt-8">
                    <CardHeader>
                        <CardTitle className="text-neon-orange">
                            API Integration
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2 text-sm text-gray-300">
                            <p>
                                • <strong>Endpoint:</strong>{" "}
                                <code className="bg-gray-800 px-2 py-1 rounded">
                                    {API_BASE_URL}/topology_analyzer
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

export default TopologyAnalyzer;
