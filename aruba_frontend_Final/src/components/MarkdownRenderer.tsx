import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

export const MarkdownRenderer = ({ content }: { content: string }) => {
    return (
        <div
            className="prose prose-invert max-w-none text-sm table-fixed [&_td]:break-words [&_th]:text-neon-cyan
    [&_table]:border [&_table]:border-gray-700
    [&_th]:border [&_th]:border-gray-700
    [&_td]:border [&_td]:border-gray-700
    [&_th]:bg-gray-900
    [&_td]:bg-gray-800
    [&_ul]:mb-6 [&_ol]:mb-6
    [&_li]:mb-2"
        >
            <ReactMarkdown
                rehypePlugins={[rehypeRaw]}
                remarkPlugins={[remarkGfm]}
                components={{
                    code({ node, inline, className, children, ...props }: any) {
                        const match = /language-(\w+)/.exec(className || "");
                        return !inline && match ? (
                            <SyntaxHighlighter
                                style={oneDark}
                                language={match[1]}
                                PreTag="div"
                                className="rounded-lg"
                                {...props}
                            >
                                {String(children).replace(/\n$/, "")}
                            </SyntaxHighlighter>
                        ) : (
                            <code className="bg-gray-800 text-green-400 px-1 py-0.5 rounded">
                                {children}
                            </code>
                        );
                    },
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
};
