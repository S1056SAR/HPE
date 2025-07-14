import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
// import QueryDocumentationPage from "./pages/QueryDocumentationPage";
import VectorDatabasePage from "./pages/VectorDatabasePage";
import UrlScraperPage from "./pages/UrlScraperPage";
import WebSearchPage from "./pages/WebSearchPage";
import UrlListIngestionPage from "./pages/UrlListIngestionPage";

import RagQueryPage from "./pages/RagQueryPage";
import TopologyAnalyzer from "./pages/TopologyAnalyzerPage";
import AdminPanel from "./pages/AdminPanel";

const queryClient = new QueryClient();

const App = () => (
    <QueryClientProvider client={queryClient}>
        <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Index />} />
                    <Route path="/admin" element={<AdminPanel />} />
                    {/* <Route path="/query-documentation" element={<QueryDocumentationPage />} /> */}
                    <Route path="/query-rag" element={<RagQueryPage />} />
                    <Route
                        path="/topology-analyzer"
                        element={<TopologyAnalyzer />}
                    />
                    <Route
                        path="/vector-database"
                        element={<VectorDatabasePage />}
                    />
                    <Route path="/url-scraper" element={<UrlScraperPage />} />
                    <Route path="/web-search" element={<WebSearchPage />} />
                    <Route
                        path="/url-ingestion"
                        element={<UrlListIngestionPage />}
                    />
                    {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                    <Route path="*" element={<NotFound />} />
                </Routes>
            </BrowserRouter>
        </TooltipProvider>
    </QueryClientProvider>
);

export default App;
