import { useState } from "react";
import { Header } from "@/components/Header";
import { ServiceCard } from "@/components/ServiceCard";
import { ChatInterface } from "@/components/ChatInterface";
import {
    Search,
    Database,
    Globe,
    Link,
    FileText,
    MessageCircle,
    Bot,
    Network,
} from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const Index = () => {
    const [activeService, setActiveService] = useState<string | null>(null);

    const services = [
        {
            id: "query_rag",
            title: "Agentic RAG Search",
            description: "Search using the Agentic RAG Pipeline",
            icon: Bot,
            color: "neon-red",
            apiEndpoint: "/query_rag",
        },
        {
            id: "topology_analyzer",
            title: "Network Topology Related Query Analysis",
            description: "Query along with the network topology",
            icon: Network,
            color: "neon-green",
            apiEndpoint: "/topology-analyzer",
        },
        // {
        //     id: "query_documentation",
        //     title: "Query Documentation",
        //     description:
        //         "Search through technical documentation and knowledge base",
        //     icon: FileText,
        //     color: "neon-blue",
        //     apiEndpoint: "// Insert API URL for documentation queries here",
        // },
        // {
        //     id: "search_vector_database",
        //     title: "Vector Database Search",
        //     description: "Semantic search through vector embeddings",
        //     icon: Database,
        //     color: "neon-cyan",
        //     apiEndpoint: "// Insert API URL for vector database search here",
        // },
        // {
        //     id: "scrape_url",
        //     title: "URL Scraper",
        //     description: "Extract and analyze content from web pages",
        //     icon: Link,
        //     color: "neon-green",
        //     apiEndpoint: "// Insert API URL for URL scraping here",
        // },
        // {
        //     id: "web_search",
        //     title: "Web Search",
        //     description: "Search the web for relevant information",
        //     icon: Search,
        //     color: "neon-purple",
        //     apiEndpoint: "// Insert API URL for web search here",
        // },
        // {
        //     id: "ingest_url_list",
        //     title: "URL List Ingestion",
        //     description: "Bulk process and ingest multiple URLs",
        //     icon: Globe,
        //     color: "neon-orange",
        //     apiEndpoint: "// Insert API URL for URL list ingestion here",
        // },
    ];

    return (
        <div className="min-h-screen bg-black">
            <Header />

            <main className="container mx-auto px-4 py-8">
                {/* Hero Section */}
                <div className="text-center mb-12 animate-slide-in">
                    <h1 className="text-5xl md:text-7xl font-bold mb-6 neon-text animate-neon-text">
                        ARUBA NETWORKS
                    </h1>
                    <p className="text-xl md:text-2xl text-gray-300 mb-8">
                        AI-Powered Network Intelligence Platform
                    </p>
                    <div className="w-32 h-1 bg-gradient-to-r from-neon-blue to-neon-cyan mx-auto rounded-full"></div>
                </div>

                {/* Chat Interface */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-6">
                        <MessageCircle className="w-8 h-8 text-neon-blue" />
                        <h2 className="text-3xl font-bold neon-text">
                            AI Assistant
                        </h2>
                    </div>
                    <ChatInterface />
                </div>

                {/* Services Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                    {services.map((service, index) => (
                        <ServiceCard
                            key={service.id}
                            service={service}
                            index={index}
                            onClick={() => setActiveService(service.id)}
                            isActive={activeService === service.id}
                        />
                    ))}
                </div>

                {/* API Integration Notes */}
                <div className="glass-morphism rounded-xl p-6 mt-12">
                    <h3 className="text-xl font-bold text-neon-blue mb-4">
                        API Integration Points
                    </h3>
                    <div className="space-y-2 text-sm text-gray-300">
                        <p>
                            • <strong>Base API URL:</strong>{" "}
                            <code className="bg-gray-800 px-2 py-1 rounded">
                                {API_BASE_URL}
                            </code>
                        </p>
                        {/* <p>
                            • <strong>Authentication:</strong>{" "}
                            <code className="bg-gray-800 px-2 py-1 rounded">
                                // Add your API authentication headers here
                            </code>
                        </p> */}
                        {/* <p>
                            • <strong>Chat Endpoint:</strong>{" "}
                            <code className="bg-gray-800 px-2 py-1 rounded">
                                // Insert chatbot API endpoint here
                            </code>
                        </p> */}
                        <p>
                            • Each service card contains its specific API
                            endpoint in the component props
                        </p>
                        {/* <p>
                            • WebSocket connection for real-time chat:{" "}
                            <code className="bg-gray-800 px-2 py-1 rounded">
                                // Insert WebSocket URL here
                            </code>
                        </p> */}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Index;
