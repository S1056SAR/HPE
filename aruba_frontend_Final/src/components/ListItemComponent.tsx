import { LucideIcon } from "lucide-react";
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

interface ListItemComponentProps {
    service: Service;
    index: number;
    onClick: () => void;
    isActive: boolean;
}

export const ListItemComponent = ({
    service,
    index,
    onClick,
    isActive,
}: ListItemComponentProps) => {
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
        // Simulate API call
        setTimeout(() => {
            setIsLoading(false);
            navigate(getServiceRoute(service.id));
        }, 1000);
    };

    const getColorClasses = (color: string) => {
        const colorMap = {
            "neon-blue": "text-neon-blue",
            "neon-cyan": "text-neon-cyan",
            "neon-green": "text-neon-green",
            "neon-purple": "text-neon-purple",
            "neon-pink": "text-neon-pink",
            "neon-orange": "text-neon-orange",
            "neon-red": "text-neon-red",
        };
        return colorMap[color as keyof typeof colorMap] || colorMap["neon-blue"];
    };

    const Icon = service.icon;

    return (
        <div
            className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors
                ${isActive ? "bg-black/30 border-l-4 border-neon-blue scale-105" : "hover:bg-black/10"}
            `}
            style={{ animationDelay: `${index * 50}ms` }}
            onClick={onClick}
        >
            <div className={`mr-4 p-2 rounded ${getColorClasses(service.color)} bg-black/40`}>
                <Icon className="w-5 h-5" />
            </div>
            <div className="flex-1">
                <div className="flex items-center">
                    <span className="font-semibold text-white">{service.title}</span>
                    {isActive && (
                        <span className="ml-2 px-2 py-0.5 text-xs rounded bg-neon-blue/20 text-neon-blue">
                            Active
                        </span>
                    )}
                </div>
                <div className="text-gray-400 text-xs">{service.description}</div>
                <div className="text-xs text-gray-500 mt-1">
                    <code>{service.apiEndpoint}</code>
                </div>
            </div>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    handleServiceCall();
                }}
                disabled={isLoading}
                className={`ml-4 px-3 py-1 rounded border border-gray-700 text-white text-sm
                    hover:border-neon-blue hover:text-neon-blue transition-all duration-200
                    ${isLoading ? "opacity-60 cursor-not-allowed" : ""}
                `}
            >
                {isLoading ? (
                    <span className="flex items-center space-x-1">
                        <span className="w-3 h-3 border-2 border-neon-blue border-t-transparent rounded-full animate-spin"></span>
                        <span>Opening...</span>
                    </span>
                ) : (
                    "Open"
                )}
            </button>
        </div>
    );
};
