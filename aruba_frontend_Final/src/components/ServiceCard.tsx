import { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

interface Service {
    id: string;
    title: string;
    description: string;
    icon: LucideIcon;
    color: string;
    apiEndpoint: string;
}

interface ServiceCardProps {
    service: Service;
    index: number;
    onClick: () => void;
    isActive: boolean;
}

export const ServiceCard = ({
    service,
    index,
    onClick,
    isActive,
}: ServiceCardProps) => {
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const getServiceRoute = (serviceId: string) => {
        const routeMap: { [key: string]: string } = {
            query_rag: "/query-rag",
            topology_analyzer: "/topology-analyzer",
            query_documentation: "/query-documentation",
            search_vector_database: "/vector-database",
            scrape_url: "/url-scraper",
            web_search: "/web-search",
            ingest_url_list: "/url-ingestion",
        };
        return routeMap[serviceId] || "/";
    };

    const handleServiceCall = async () => {
        setIsLoading(true);

        // TODO: Replace with actual API call
        console.log(`Calling service: ${service.id}`);
        console.log(`API Endpoint: ${service.apiEndpoint}`);

        // Simulate API call
        setTimeout(() => {
            setIsLoading(false);
            // Navigate to the service page
            navigate(getServiceRoute(service.id));
        }, 1000);
    };

    const getColorClasses = (color: string) => {
        const colorMap = {
            "neon-blue":
                "border-neon-blue text-neon-blue hover:shadow-neon-blue/20",
            "neon-cyan":
                "border-neon-cyan text-neon-cyan hover:shadow-neon-cyan/20",
            "neon-green":
                "border-neon-green text-neon-green hover:shadow-neon-green/20",
            "neon-purple":
                "border-neon-purple text-neon-purple hover:shadow-neon-purple/20",
            "neon-pink":
                "border-neon-pink text-neon-pink hover:shadow-neon-pink/20",
            "neon-orange":
                "border-neon-orange text-neon-orange hover:shadow-neon-orange/20",
            "neon-red":
                "border-neon-red text-neon-red hover:shadow-neon-red/20",
        };
        return (
            colorMap[color as keyof typeof colorMap] || colorMap["neon-blue"]
        );
    };

    const Icon = service.icon;

    return (
        <div
            className={`service-card group cursor-pointer ${
                isActive ? "neon-border scale-105" : ""
            }`}
            style={{ animationDelay: `${index * 100}ms` }}
            onClick={onClick}
        >
            <div className="flex items-start justify-between mb-4">
                <div
                    className={`p-3 rounded-lg bg-black/50 ${getColorClasses(
                        service.color
                    )}`}
                >
                    <Icon className="w-6 h-6" />
                </div>
                <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-neon-green rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full"></div>
                    <div className="w-2 h-2 bg-gray-600 rounded-full"></div>
                </div>
            </div>

            <h3 className="text-xl font-bold text-white mb-2 group-hover:text-neon-blue transition-colors">
                {service.title}
            </h3>

            <p className="text-gray-400 mb-6 text-sm leading-relaxed">
                {service.description}
            </p>

            <div className="space-y-3">
                <Button
                    onClick={(e) => {
                        e.stopPropagation();
                        handleServiceCall();
                    }}
                    disabled={isLoading}
                    className="w-full bg-transparent border border-gray-700 text-white hover:border-neon-blue hover:text-neon-blue hover:shadow-lg hover:shadow-neon-blue/20 transition-all duration-300"
                >
                    {isLoading ? (
                        <div className="flex items-center space-x-2">
                            <div className="w-4 h-4 border-2 border-neon-blue border-t-transparent rounded-full animate-spin"></div>
                            <span>Opening...</span>
                        </div>
                    ) : (
                        "Open Service"
                    )}
                </Button>

                <div className="text-xs text-gray-500 bg-gray-900/50 p-2 rounded border">
                    <code>{service.apiEndpoint}</code>
                </div>
            </div>
        </div>
    );
};
