import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TimelineItem } from "./TimelineItem";
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
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold tracking-tight">XTimeline</h1>
              <p className="text-xs text-muted-foreground">
                Build fact-based timelines from X data
              </p>
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
        {/* Search Section */}
        <section className="mb-8">
          <Card className="bg-card/50 backdrop-blur-sm border-border">
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
                <Button onClick={handleSearch} disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Search className="mr-2 h-4 w-4" />
                      Generate
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
              <Card className="bg-card/50 backdrop-blur-sm border-border">
                <CardContent className="pt-12 pb-12">
                  <div className="text-center">
                    <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                      <Search className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">
                      Search for a topic
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Try: "Mumbai floods 2026" or "Maharashtra elections"
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {loading && (
              <Card className="bg-card/50 backdrop-blur-sm border-border">
                <CardContent className="pt-12 pb-12">
                  <div className="text-center">
                    <Loader2 className="mx-auto h-8 w-8 animate-spin text-muted-foreground mb-4" />
                    <p className="text-sm text-muted-foreground">
                      Generating timeline...
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {timeline && (
              <div className="space-y-4">
                <Card className="bg-card/50 backdrop-blur-sm border-border">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">
                      {timeline.topic || "Timeline"}
                    </CardTitle>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>
                        {timeline.events?.length || 0} events
                      </span>
                      <span>•</span>
                      <span>
                        Avg. credibility:{" "}
                        {Math.round((timeline.avg_credibility || 0) * 100)}%
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className">
                      {/* Timeline="relative line */}
                      <div className="absolute left-[11px] top-0 bottom-0 w-px bg-border" />
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
              <Card className="bg-card/50 backdrop-blur-sm border-border">
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
              <Card className="bg-card/50 backdrop-blur-sm border-border">
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
            <Card className="bg-card/50 backdrop-blur-sm border-border">
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
      <footer className="border-t border-border mt-12 py-6">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <p>Chronofact.ai</p>
            <a
              href="https://github.com/Ayush4513/Chronofact.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              GitHub
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
