import React from "react";
import { useState, useRef, useEffect } from "react";
import { Send, User, Loader2, ImageIcon, CloudCog } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { MarkdownRenderer } from "./MarkdownRenderer";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface Message {
    id: string;
    text: string;
    sender: "user" | "ai";
    timestamp: Date;
}

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
        apiEndpoint: "/topology/analyze-topology",
    },
    {
        id: "web_search",
        title: "Web Search",
        description: "Search the web for relevant information",
        icon: Search,
        color: "neon-purple",
        apiEndpoint: "// Insert API URL for web search here",
    },
];

export const ChatInterface = () => {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: "1",
            text: "Hello! I'm your Aruba Networks AI assistant. I can help you with network management, documentation queries, and technical support. How can I assist you today?",
            sender: "ai",
            timestamp: new Date(),
        },
    ]);

    const [inputText, setInputText] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);

    const [service, setService] = useState("auto");
    const [file, setFile] = useState<File | null>(null);
    const [imageBase64, setImageBase64] = useState<string | null>(null);

    const filePreviewRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        // messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        chatContainerRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputText.trim()) return;
        setIsLoading(true);

        // Add user message to chat
        const userMessage: Message = {
            id: Date.now().toString(),
            text: inputText,
            sender: "user",
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setInputText("");

        try {
            const response = await fetch(`${API_BASE_URL}/rag/agentic_query`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: userMessage.text,
                    use_orchestrator: true,
                }),
            });
            if (!response.ok) throw new Error("API error");
            const data = await response.json();
            // Assume the backend returns the answer in data.response or data.result
            const aiText = data.response || data.result || JSON.stringify(data);
            const aiMessage: Message = {
                id: (Date.now() + 1).toString(),
                text: aiText,
                sender: "ai",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
            setMessages((prev) => [
                ...prev,
                {
                    id: (Date.now() + 2).toString(),
                    text: "Sorry, there was an error contacting the backend API.",
                    sender: "ai",
                    timestamp: new Date(),
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    // NEED TO CONFIRM.
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith("image/")) {
            alert("Please upload a valid image file.");
            return;
        }

        setFile(file);

        const reader = new FileReader();
        reader.onload = (e) => {
            if (filePreviewRef.current) {
                filePreviewRef.current.innerHTML = `
                    <h5 class="text-sm text-neon-blue text-gray-300 mt-2 mb-4 px-4">Input Image</h5>
                    <img src="${e.target?.result}" alt="Preview" class="max-h-10 rounded" />
                    <p class="text-sm text-gray-300 mt-2">${file.name}</p>
                `;
            }
        };
        reader.readAsDataURL(file);
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const getAPIEndpoint = () => {
        if (service === "auto") {
            if (file) {
                services.find((s) => s.id === "topology_analyzer")?.apiEndpoint;
            }
            return services.find((s) => s.id === "query_rag")?.apiEndpoint;
        }
        return services.find((s) => s.id === service)?.apiEndpoint;
    };

    const buildPayload = () => {
        if (file && imageBase64) {
            // Need to opt for Topology Analysis.
            return {
                name: "analyze_topology",
                arguments: {
                    image_data: imageBase64.split(",")[1],
                    replacement_query: inputText,
                },
                session: {},
            };
        }

        // Standard tool query.
        let toolName = service;
        if (service === "auto") {
            toolName = "query_documentation";
        }
        return {
            name: toolName,
            arguments: {
                query: inputText,
                vendor: "aruba",
            },
        };
    };

    return (
        <div className="w-full max-w-4xl mx-auto chat-wrapper glass-morphism rounded-xl overflow-hidden min-h-0 max-h-[80vh] flex flex-col">
            {/* <div className="chat-wrapper glass-morphism rounded-xl overflow-hidden h-96 flex flex-col"> */}
            {/* Chat Header */}
            <div className="chat-header bg-gray-900/50 px-6 py-4 border-b border-gray-800">
                <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-neon-blue to-neon-cyan rounded-full flex items-center justify-center">
                        <Bot className="w-6 h-6 text-black" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">
                            Aruba AI Assistant
                        </h3>
                        <p className="text-sm text-gray-400">
                            Online • Ready to help
                        </p>
                    </div>
                </div>
            </div>

            {/* Messages Area */}
            <div
                ref={chatContainerRef}
                className="chat-section-container flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-neon-blue scrollbar-track-gray-800"
            >
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex items-start space-x-3 ${
                            message.sender === "user"
                                ? "flex-row-reverse space-x-reverse"
                                : ""
                        }`}
                    >
                        <div
                            className={`w-6 h-8 rounded-full flex items-center justify-center ${
                                message.sender === "user"
                                    ? "bg-neon-blue text-black"
                                    : "bg-gray-800 text-neon-blue"
                            }`}
                        >
                            {message.sender === "user" ? (
                                <User className="w-4 h-4" />
                            ) : (
                                <Bot className="w-4 h-4" />
                            )}
                        </div>

                        <div
                            className={`max-w-xl lg:max-w-3xl p-4 ${
                                // className={`max-w-md lg:max-w-md ${
                                message.sender === "user"
                                    ? "chat-bubble-user"
                                    : "chat-bubble-ai"
                            }`}
                        >
                            {/* <p className="chat-message text-sm">{message.text}</p> */}
                            <div className="chat-message text-base leading-relaxed space-y-4 ">
                                <MarkdownRenderer content={message.text} />
                            </div>
                            <p
                                className={`timestamp text-xs mt-1 opacity-70 ${
                                    message.sender === "user"
                                        ? "text-black"
                                        : "text-gray-400"
                                }`}
                            >
                                {message.timestamp.toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })}
                            </p>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 bg-gray-800 text-neon-blue rounded-full flex items-center justify-center">
                            <Bot className="w-4 h-4" />
                        </div>
                        <div className="chat-bubble-ai">
                            <div className="flex items-center space-x-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span className="text-sm">
                                    AI is thinking...
                                </span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="chat-input bg-gray-900/50 px-6 py-4 border-t border-gray-800">
                {/* Image Preview */}
                <div ref={filePreviewRef} className="mb-2"></div>

                {/* Services - Menu */}
                {/* <div className="flex items-center space-x-3 mb-2">
                    <label
                        htmlFor="service-select"
                        className="text-xs text-gray-400"
                    >
                        Service:
                    </label>
                    <select
                        id="service-select"
                        value={service}
                        onChange={(e) => setService(e.target.value)}
                        className="bg-gray-800 border border-gray-700 text-white rounded px-2 py-1 focus:border-neon-blue"
                        disabled={isLoading}
                    >
                        <option value="auto">Auto (let AI choose)</option>
                        {services.map((s) => (
                            <option key={s.id} value={s.id}>
                                {s.title}
                            </option>
                        ))}
                    </select>
                </div> */}

                {/* Service-Message */}
                <div className="flex items-center space-x-2 mb-2">
                    {service !== "auto" && (
                        <>
                            <div className="w-5 h-5 flex items-center justify-center">
                                {services.find((s) => s.id === service)?.icon &&
                                    React.createElement(
                                        services.find((s) => s.id === service)
                                            .icon,
                                        {
                                            className: "w-4 h-4 text-neon-blue",
                                        }
                                    )}
                            </div>
                            <span className="text-xs text-neon-blue font-semibold">
                                {services.find((s) => s.id === service)?.title}
                            </span>
                            <span className="text-xs text-gray-400">
                                (
                                {
                                    services.find((s) => s.id === service)
                                        ?.description
                                }
                                )
                            </span>
                        </>
                    )}
                    {service === "auto" && (
                        <span className="text-xs text-gray-400">
                            <strong>Auto mode:</strong> The assistant will
                            choose the best service based on your input.
                        </span>
                    )}
                </div>

                {/* Input Field */}
                <div className="flex items-center space-x-2">
                    <input
                        className="mb-4"
                        type="file"
                        accept="image/*"
                        id="image-upload"
                        style={{ display: "none" }}
                        onChange={handleFileChange}
                    />
                    <label htmlFor="image-upload" className="cursor-pointer">
                        <ImageIcon className="w-8 h-8 text-gray-400 hover:text-neon-blue" />
                    </label>
                    <Input
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask me anything about Aruba Networks..."
                        className="flex-1 bg-gray-800 border-gray-700 text-white placeholder-gray-400 focus:border-neon-blue focus:ring-neon-blue"
                        disabled={isLoading}
                    />
                    <Button
                        onClick={handleSendMessage}
                        disabled={!inputText.trim() || isLoading}
                        className="bg-neon-blue text-black hover:bg-neon-cyan transition-colors px-6"
                    >
                        <Send className="w-4 h-4" />
                    </Button>
                </div>

                {/* API Integration Note */}
                <div className="mt-2 text-xs text-gray-500">
                    <strong>API Integration:</strong> Connect to{" "}
                    <code className="bg-gray-800 px-1 rounded">
                        {API_BASE_URL}
                    </code>
                </div>
            </div>
        </div>
    );
};
