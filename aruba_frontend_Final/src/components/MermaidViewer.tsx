import { useEffect, useRef } from "react";
import mermaid from "mermaid";
import { Button } from "@/components/ui/button";
import { ClipboardCopy, Download } from "lucide-react";

interface MermaidViewerProps {
    code: string;
    title?: string;
    pngUrl?: string;
    svgUrl?: string;
}

export const MermaidViewer: React.FC<MermaidViewerProps> = ({
    code,
    title,
    pngUrl,
    svgUrl,
}) => {
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (containerRef.current) {
            containerRef.current.innerHTML = `<div class="mermaid">${code}</div>`;
            mermaid.initialize({ startOnLoad: false });
            mermaid.run(undefined, containerRef.current);
        }
    }, [code]);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        alert("Mermaid code copied to clipboard!");
    };

    const handleDownload = () => {
        const blob = new Blob([code], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${title || "diagram"}.mmd`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleImageDownload = (url: string, format: "png" | "svg") => {
        const a = document.createElement("a");
        a.href = url;
        a.download = `${title || "diagram"}.${format}`;
        a.click();
    };

    return (
        <div className="bg-gray-900 rounded-lg p-4 border border-gray-700 mb-4">
            {title && (
                <h3 className="text-lg font-semibold text-neon-cyan mb-2">
                    {title}
                </h3>
            )}
            <div ref={containerRef} className="overflow-x-auto mb-4" />
            <div className="flex gap-2">
                <Button
                    onClick={handleCopy}
                    variant="outline"
                    className="text-white border-gray-600 hover:border-neon-blue"
                >
                    <ClipboardCopy className="w-4 h-4 mr-2" /> Copy Code
                </Button>
                <Button
                    onClick={handleDownload}
                    variant="outline"
                    className="text-white border-gray-600 hover:border-neon-blue"
                >
                    <Download className="w-4 h-4 mr-2" /> Download .mmd
                </Button>
            </div>
            {(pngUrl || svgUrl) && (
                <div className="flex gap-2 mt-2">
                    {pngUrl && (
                        <Button
                            onClick={() => handleImageDownload(pngUrl, "png")}
                            variant="secondary"
                            className="text-white bg-gray-700 hover:bg-neon-blue"
                        >
                            🖼️ Download PNG
                        </Button>
                    )}
                    {svgUrl && (
                        <Button
                            onClick={() => handleImageDownload(svgUrl, "svg")}
                            variant="secondary"
                            className="text-white bg-gray-700 hover:bg-neon-cyan"
                        >
                            Download SVG
                        </Button>
                    )}
                </div>
            )}
        </div>
    );
};
