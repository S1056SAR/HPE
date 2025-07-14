
import { useState } from 'react';
import { Header } from '@/components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Link as LinkIcon, ArrowLeft, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';

const UrlScraperPage = () => {
  const [url, setUrl] = useState('');
  const [results, setResults] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleScrape = async () => {
    setIsLoading(true);
    
    // TODO: Replace with actual API call
    console.log('Scraping URL:', url);
    console.log('API Endpoint: // Insert API URL for URL scraping here');
    
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setResults({
        title: 'Sample Website Title',
        description: 'This is a sample description extracted from the website.',
        content: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit...',
        metadata: {
          wordCount: 1250,
          imageCount: 5,
          linkCount: 23
        }
      });
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-black">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link to="/">
            <Button variant="outline" className="bg-transparent border-gray-700 text-white hover:border-neon-green">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg bg-black/50 border-neon-green text-neon-green border">
              <LinkIcon className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-bold neon-text">URL Scraper</h1>
              <p className="text-gray-400">Extract and analyze content from web pages</p>
            </div>
          </div>
        </div>

        {/* Scrape Interface */}
        <Card className="glass-morphism mb-8">
          <CardHeader>
            <CardTitle className="text-neon-green">Web Content Extraction</CardTitle>
            <CardDescription>Enter a URL to scrape and analyze its content</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com"
                className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:border-neon-green focus:outline-none"
              />
              <Button 
                onClick={handleScrape}
                disabled={isLoading || !url.trim()}
                className="bg-neon-green text-black hover:bg-neon-cyan"
              >
                {isLoading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                    <span>Scraping...</span>
                  </div>
                ) : (
                  <>
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Scrape URL
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {results && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold text-neon-green">Extracted Content</h2>
            
            <Card className="glass-morphism">
              <CardHeader>
                <CardTitle className="text-white">{results.title}</CardTitle>
                <CardDescription>{results.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300 mb-4">{results.content}</p>
                
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="text-center p-4 bg-gray-900/50 rounded-lg">
                    <div className="text-2xl font-bold text-neon-green">{results.metadata.wordCount}</div>
                    <div className="text-sm text-gray-400">Words</div>
                  </div>
                  <div className="text-center p-4 bg-gray-900/50 rounded-lg">
                    <div className="text-2xl font-bold text-neon-green">{results.metadata.imageCount}</div>
                    <div className="text-sm text-gray-400">Images</div>
                  </div>
                  <div className="text-center p-4 bg-gray-900/50 rounded-lg">
                    <div className="text-2xl font-bold text-neon-green">{results.metadata.linkCount}</div>
                    <div className="text-sm text-gray-400">Links</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* API Integration Info */}
        <Card className="glass-morphism mt-8">
          <CardHeader>
            <CardTitle className="text-neon-orange">🔧 API Integration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm text-gray-300">
              <p>• <strong>Endpoint:</strong> <code className="bg-gray-800 px-2 py-1 rounded">// Insert API URL for URL scraping here</code></p>
              <p>• <strong>Method:</strong> POST</p>
              <p>• <strong>Headers:</strong> Authorization, Content-Type</p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default UrlScraperPage;
