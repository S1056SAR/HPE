
import { useState } from 'react';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Globe, ArrowLeft, Upload, CheckCircle, XCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

const UrlListIngestionPage = () => {
  const [urls, setUrls] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleIngest = async () => {
    setIsLoading(true);
    
    // TODO: Replace with actual API call
    console.log('Ingesting URL list:', urls.split('\n').filter(url => url.trim()));
    console.log('API Endpoint: // Insert API URL for URL list ingestion here');
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      const urlList = urls.split('\n').filter(url => url.trim());
      setResults(urlList.map((url, index) => ({
        url: url.trim(),
        status: Math.random() > 0.2 ? 'success' : 'failed',
        documentsExtracted: Math.floor(Math.random() * 50) + 1,
        processingTime: (Math.random() * 5 + 1).toFixed(2) + 's'
      })));
    }, 4000);
  };

  return (
    <div className="min-h-screen bg-black">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link to="/">
            <Button variant="outline" className="bg-transparent border-gray-700 text-white hover:border-neon-orange">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-black/50 border-neon-orange text-neon-orange border">
              <Globe className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold neon-text">URL List Ingestion</h1>
              <p className="text-gray-400">Bulk process and ingest multiple URLs</p>
            </div>
          </div>
        </div>

        {/* Input Interface */}
        <Card className="glass-morphism mb-8">
          <CardHeader>
            <CardTitle className="text-neon-orange">Bulk URL Processing</CardTitle>
            <CardDescription>Enter multiple URLs (one per line) for batch ingestion</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <textarea
                value={urls}
                onChange={(e) => setUrls(e.target.value)}
                placeholder="https://example1.com&#10;https://example2.com&#10;https://example3.com"
                rows={8}
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-orange focus:outline-none resize-vertical"
              />
              <Button 
                onClick={handleIngest}
                disabled={isLoading || !urls.trim()}
                className="bg-neon-orange text-black hover:bg-neon-green"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                    <span>Processing URLs...</span>
                  </div>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Ingest URLs
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-neon-orange">Processing Results</h2>
            
            {/* Summary */}
            <Card className="glass-morphism">
              <CardContent className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-neon-green">
                      {results.filter(r => r.status === 'success').length}
                    </div>
                    <div className="text-sm text-gray-400">Successful</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-neon-orange">
                      {results.filter(r => r.status === 'failed').length}
                    </div>
                    <div className="text-sm text-gray-400">Failed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">{results.length}</div>
                    <div className="text-sm text-gray-400">Total URLs</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Results */}
            <div className="space-y-2">
              {results.map((result, index) => (
                <Card key={index} className="glass-morphism">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          {result.status === 'success' ? (
                            <CheckCircle className="w-5 h-5 text-neon-green" />
                          ) : (
                            <XCircle className="w-5 h-5 text-neon-orange" />
                          )}
                          <span className="text-white text-sm">{result.url}</span>
                        </div>
                        {result.status === 'success' && (
                          <div className="text-xs text-gray-400 ml-7">
                            {result.documentsExtracted} documents extracted in {result.processingTime}
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* API Integration Info */}
        <Card className="glass-morphism mt-8">
          <CardHeader>
            <CardTitle className="text-neon-orange">🔧 API Integration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-gray-300">
              <p>• <strong>Endpoint:</strong> <code className="bg-gray-800 px-2 py-1 rounded">// Insert API URL for URL list ingestion here</code></p>
              <p>• <strong>Method:</strong> POST</p>
              <p>• <strong>Headers:</strong> Authorization, Content-Type</p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default UrlListIngestionPage;
