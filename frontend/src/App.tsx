import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TimelineItem } from "./components/TimelineItem";
import { api, Timeline, MisinformationAnalysis, Recommendation } from "@/lib/api";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Search,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lightbulb,
  ExternalLink,
} from "lucide-react";

export function App() {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(10);
  const [loading, setLoading] = useState(false);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [detectResult, setDetectResult] =
    useState<MisinformationAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [apiStatus, setApiStatus] = useState<"checking" | "connected" | "disconnected">(
    "checking"
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkApiStatus();
  }, []);

  const checkApiStatus = async () => {
    try {
      const health = await api.healthCheck();
      setApiStatus(
        health.qdrant_connected && health.baml_available
          ? "connected"
          : "disconnected"
      );
    } catch {
      setApiStatus("disconnected");
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setDetectResult(null);
    setRecommendations([]);

    try {
      const result = await api.generateTimeline({
        topic: query,
        limit,
      });
      setTimeline(result);

      if (result.events && result.events.length > 0) {
        await runAnalysis(query);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate timeline");
      setTimeline(null);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async (searchQuery: string) => {
    try {
      const [detectResult, recommendationsResult] = await Promise.all([
        api.detectMisinformation(searchQuery),
        api.getRecommendations({ query: searchQuery, limit: 5 }),
      ]);
      setDetectResult(detectResult);
      setRecommendations(recommendationsResult.recommendations || []);
    } catch (err) {
      console.warn("Analysis error:", err);
    }
  };

  const handleRecommendationClick = (action: string) => {
    setQuery(action);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      {/* Decorative background elements */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-400/10 rounded-full blur-3xl"></div>
      </div>
      
      {/* Header */}
      <header className="border-b border-border/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-lg">C</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Chronofact.ai
                </h1>
                <p className="text-xs text-muted-foreground">
                  AI-Powered Fact-Based Timeline Generator
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "w-2 h-2 rounded-full",
                  apiStatus === "connected" && "bg-emerald-500",
                  apiStatus === "disconnected" && "bg-red-500",
                  apiStatus === "checking" && "bg-amber-500 animate-pulse"
                )}
              />
              <span className="text-xs text-muted-foreground capitalize">
                {apiStatus === "connected"
                  ? "Connected"
                  : apiStatus === "disconnected"
                  ? "Disconnected"
                  : "Checking..."}
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Hero Section */}
        <section className="mb-12 text-center py-8">
          <div className="max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100/50 dark:bg-blue-900/20 border border-blue-200/50 dark:border-blue-800/50 mb-6">
              <CheckCircle2 className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                Powered by Qdrant & BAML
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent animate-gradient">
              Discover Truth Through Time
            </h2>
            <p className="text-lg text-muted-foreground mb-8">
              Build accurate, verifiable event timelines with AI-powered fact-checking and credibility assessment
            </p>
          </div>
        </section>

        {/* Search Section */}
        <section className="mb-8">
          <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-border/50 shadow-xl">
            <CardContent className="pt-6">
              <div className="flex gap-4 mb-4">
                <div className="flex-1">
                  <Label htmlFor="search" className="sr-only">
                    Search topics
                  </Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="search"
                      placeholder="Search topics, events, or locations..."
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                      className="pl-10 bg-background/50"
                    />
                  </div>
                </div>
                <div className="w-24">
                  <Label htmlFor="limit" className="sr-only">
                    Number of events
                  </Label>
                  <Input
                    id="limit"
                    type="number"
                    min={3}
                    max={50}
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="bg-background/50"
                  />
                </div>
                <Button 
                  onClick={handleSearch} 
                  disabled={loading}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Search className="mr-2 h-4 w-4" />
                      Generate Timeline
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Error Message */}
        {error && (
          <Card className="mb-6 bg-destructive/10 border-destructive/20">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-destructive">
                <XCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline Section */}
          <div className="lg:col-span-2">
            {!timeline && !loading && (
              <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-border/50 shadow-xl">
                <CardContent className="pt-16 pb-16">
                  <div className="text-center">
                    <div className="mx-auto w-24 h-24 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg">
                      <Search className="h-12 w-12 text-white" />
                    </div>
                    <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                      Ready to Explore?
                    </h3>
                    <p className="text-base text-muted-foreground mb-6">
                      Enter a topic above to generate a fact-checked timeline
                    </p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      <span className="px-3 py-1.5 rounded-full bg-blue-100/50 dark:bg-blue-900/20 text-sm text-blue-700 dark:text-blue-300 border border-blue-200/50 dark:border-blue-800/50">
                        Mumbai floods 2026
                      </span>
                      <span className="px-3 py-1.5 rounded-full bg-purple-100/50 dark:bg-purple-900/20 text-sm text-purple-700 dark:text-purple-300 border border-purple-200/50 dark:border-purple-800/50">
                        Maharashtra elections
                      </span>
                      <span className="px-3 py-1.5 rounded-full bg-indigo-100/50 dark:bg-indigo-900/20 text-sm text-indigo-700 dark:text-indigo-300 border border-indigo-200/50 dark:border-indigo-800/50">
                        Breaking news
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {loading && (
              <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-border/50 shadow-xl">
                <CardContent className="pt-16 pb-16">
                  <div className="text-center">
                    <div className="mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg">
                      <Loader2 className="h-10 w-10 animate-spin text-white" />
                    </div>
                    <h3 className="text-xl font-semibold mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                      Generating Timeline
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Analyzing sources and building your fact-checked timeline...
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {timeline && (
              <div className="space-y-4">
                <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-border/50 shadow-xl">
                  <CardHeader className="pb-4 border-b border-border/50">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-2xl font-bold mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                          {timeline.topic || "Timeline"}
                        </CardTitle>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-100/50 dark:bg-blue-900/20 border border-blue-200/50 dark:border-blue-800/50">
                            <CheckCircle2 className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                            <span className="font-medium text-blue-700 dark:text-blue-300">
                              {timeline.events?.length || 0} Events
                            </span>
                          </div>
                          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-100/50 dark:bg-purple-900/20 border border-purple-200/50 dark:border-purple-800/50">
                            <span className="font-medium text-purple-700 dark:text-purple-300">
                              {Math.round((timeline.avg_credibility || 0) * 100)}% Credible
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="relative">
                      {/* Timeline line with gradient */}
                      <div className="absolute left-[13.5px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-400/40 via-purple-400/40 to-transparent" />
                      {timeline.events?.map((event, index) => (
                        <TimelineItem key={index} event={event} index={index} />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Misinformation Detection */}
            {detectResult && (
              <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-border/50 shadow-xl">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4" />
                    Misinformation Detection
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">
                      Risk Level
                    </span>
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium",
                        detectResult.risk_level?.toLowerCase() === "low" &&
                          "bg-emerald-500/15 text-emerald-400",
                        detectResult.risk_level?.toLowerCase() === "medium" &&
                          "bg-amber-500/15 text-amber-400",
                        detectResult.risk_level?.toLowerCase() === "high" &&
                          "bg-red-500/15 text-red-400"
                      )}
                    >
                      {detectResult.risk_level || "Unknown"}
                    </span>
                  </div>

                  {detectResult.is_suspicious !== undefined && (
                    <div className="flex items-center gap-2">
                      {detectResult.is_suspicious ? (
                        <XCircle className="h-4 w-4 text-amber-500" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      )}
                      <span className="text-sm">
                        {detectResult.is_suspicious
                          ? "Suspicious patterns detected"
                          : "No obvious issues"}
                      </span>
                    </div>
                  )}

                  {detectResult.suspicious_patterns &&
                    detectResult.suspicious_patterns.length > 0 && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">
                          Patterns
                        </p>
                        <ul className="space-y-1">
                          {detectResult.suspicious_patterns.map(
                            (pattern, index) => (
                              <li
                                key={index}
                                className="text-sm text-muted-foreground flex items-start gap-2"
                              >
                                <span className="text-muted-foreground">•</span>
                                {pattern}
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {detectResult.recommendation && (
                    <div className="pt-2 border-t border-border">
                      <p className="text-xs text-muted-foreground mb-1">
                        Recommendation
                      </p>
                      <p className="text-sm">{detectResult.recommendation}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Recommendations */}
            {recommendations.length > 0 && (
              <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-border/50 shadow-xl">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Lightbulb className="h-4 w-4" />
                    Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {recommendations.map((rec, index) => (
                    <button
                      key={index}
                      onClick={() => handleRecommendationClick(rec.action)}
                      className="w-full text-left p-3 rounded-lg bg-background/50 hover:bg-background/80 transition-colors border border-border/50 hover:border-border"
                    >
                      <p className="text-sm font-medium mb-1">{rec.action}</p>
                      <p className="text-xs text-muted-foreground">
                        {rec.reason}
                      </p>
                    </button>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* API Status Card */}
            <Card className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-border/50 shadow-xl">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">API</span>
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5",
                        apiStatus === "connected"
                          ? "text-emerald-400"
                          : "text-red-400"
                      )}
                    >
                      {apiStatus === "connected" ? (
                        <CheckCircle2 className="h-3 w-3" />
                      ) : (
                        <XCircle className="h-3 w-3" />
                      )}
                      {apiStatus === "connected"
                        ? "Connected"
                        : "Disconnected"}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 mt-16 py-8 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <div>
                <p className="font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Chronofact.ai
                </p>
                <p className="text-xs text-muted-foreground">
                  AI-Powered Fact Verification
                </p>
              </div>
            </div>
            <a
              href="https://github.com/Ayush4513/Chronofact.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors text-sm font-medium"
            >
              <span>View on GitHub</span>
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
