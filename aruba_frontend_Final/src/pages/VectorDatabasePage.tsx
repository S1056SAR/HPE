
import { useState } from 'react';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, Search, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

const VectorDatabasePage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    setIsLoading(true);
    
    // TODO: Replace with actual API call
    console.log('Searching vector database for:', query);
    console.log('API Endpoint: // Insert API URL for vector database search here');
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setResults([
        { id: 1, similarity: 0.95, content: 'Network topology configuration...', metadata: { source: 'config.json' } },
        { id: 2, similarity: 0.87, content: 'Security policy definitions...', metadata: { source: 'security.yaml' } },
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
            <Button variant="outline" className="bg-transparent border-gray-700 text-white hover:border-neon-cyan">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-black/50 border-neon-cyan text-neon-cyan border">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold neon-text">Vector Database Search</h1>
              <p className="text-gray-400">Semantic search through vector embeddings</p>
            </div>
          </div>
        </div>

        {/* Search Interface */}
        <Card className="glass-morphism mb-8">
          <CardHeader>
            <CardTitle className="text-neon-cyan">Semantic Search</CardTitle>
            <CardDescription>Enter your query for semantic vector search</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter semantic search query..."
                className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-cyan focus:outline-none"
              />
              <Button 
                onClick={handleSearch}
                disabled={isLoading || !query.trim()}
                className="bg-neon-cyan text-black hover:bg-neon-blue"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                    <span>Processing...</span>
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
            <h2 className="text-xl font-bold text-neon-cyan">Search Results</h2>
            {results.map((result) => (
              <Card key={result.id} className="glass-morphism hover:border-neon-cyan transition-colors">
                <CardContent className="p-6">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm text-neon-cyan font-semibold">Similarity: {(result.similarity * 100).toFixed(1)}%</span>
                    <span className="text-xs text-gray-500">{result.metadata.source}</span>
                  </div>
                  <p className="text-gray-300">{result.content}</p>
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
              <p>• <strong>Endpoint:</strong> <code className="bg-gray-800 px-2 py-1 rounded">// Insert API URL for vector database search here</code></p>
              <p>• <strong>Method:</strong> POST</p>
              <p>• <strong>Headers:</strong> Authorization, Content-Type</p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default VectorDatabasePage;
