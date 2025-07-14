
import { useState } from 'react';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Search, ArrowLeft, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';

const WebSearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    setIsLoading(true);
    
    // TODO: Replace with actual API call
    console.log('Searching web for:', query);
    console.log('API Endpoint: // Insert API URL for web search here');
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setResults([
        { id: 1, title: 'Aruba Networks Official Documentation', url: 'https://aruba.com/docs', snippet: 'Official documentation and guides...' },
        { id: 2, title: 'Network Configuration Best Practices', url: 'https://example.com/network-config', snippet: 'Best practices for network configuration...' },
      ]);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-black">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link to="/">
            <Button variant="outline" className="bg-transparent border-gray-700 text-white hover:border-neon-purple">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-black/50 border-neon-purple text-neon-purple border">
              <Search className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold neon-text">Web Search</h1>
              <p className="text-gray-400">Search the web for relevant information</p>
            </div>
          </div>
        </div>

        {/* Search Interface */}
        <Card className="glass-morphism mb-8">
          <CardHeader>
            <CardTitle className="text-neon-purple">Web Search Engine</CardTitle>
            <CardDescription>Search across the web for relevant information</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your search query..."
                className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-purple focus:outline-none"
              />
              <Button 
                onClick={handleSearch}
                disabled={isLoading || !query.trim()}
                className="bg-neon-purple text-black hover:bg-neon-pink"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                    <span>Searching...</span>
                  </div>
                ) : (
                  <>
                    <Globe className="w-4 h-4 mr-2" />
                    Search Web
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-neon-purple">Search Results</h2>
            {results.map((result) => (
              <Card key={result.id} className="glass-morphism hover:border-neon-purple transition-colors">
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-neon-purple mb-2">{result.title}</h3>
                  <p className="text-gray-400 mb-2">{result.snippet}</p>
                  <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-neon-cyan hover:underline text-sm">
                    {result.url}
                  </a>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* API Integration Info */}
        <Card className="glass-morphism mt-8">
          <CardHeader>
            <CardTitle className="text-neon-orange">🔧 API Integration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-gray-300">
              <p>• <strong>Endpoint:</strong> <code className="bg-gray-800 px-2 py-1 rounded">// Insert API URL for web search here</code></p>
              <p>• <strong>Method:</strong> POST</p>
              <p>• <strong>Headers:</strong> Authorization, Content-Type</p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default WebSearchPage;
