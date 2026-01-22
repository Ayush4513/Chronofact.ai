import { cn } from "@/lib/utils";

interface TimelineItemProps {
  event: {
    timestamp: string;
    summary: string;
    sources: string[];
    credibility_score: number;
    location?: string;
  };
  index: number;
}

export function TimelineItem({ event, index }: TimelineItemProps) {
  const credibility = event.credibility_score || 0;
  const credibilityPercent = Math.round(credibility * 100);

  const credibilityClass = cn(
    "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium",
    credibility >= 0.7 &&
      "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20",
    credibility >= 0.4 &&
      credibility < 0.7 &&
      "bg-amber-500/15 text-amber-400 border border-amber-500/20",
    credibility < 0.4 &&
      "bg-red-500/15 text-red-400 border border-red-500/20"
  );

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return "";
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return timestamp;
    }
  };

  const formatSources = (sources: string[]) => {
    return sources.slice(0, 3).map((source) => {
      const displaySource =
        source.length > 20 ? source.substring(0, 17) + "..." : source;
      return (
        <a
          key={source}
          href={`https://x.com/i/web/status/${source}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-muted-foreground hover:text-foreground transition-colors underline-offset-4 hover:underline"
        >
          {displaySource}
        </a>
      );
    });
  };

  return (
    <div
      className="relative pl-8 pb-8 last:pb-0 animate-in fade-in slide-in-from-bottom-2"
      style={{ animationDelay: `${index * 50}ms`, animationFillMode: "backwards" }}
    >
      {/* Timeline line */}
      <div className="absolute left-[11px] top-3 bottom-0 w-px bg-border" />

      {/* Timeline dot */}
      <div
        className={cn(
          "absolute left-0 top-1.5 w-6 h-6 rounded-full border-2 bg-background flex items-center justify-center",
          credibility >= 0.7 && "border-emerald-500/50",
          credibility >= 0.4 &&
            credibility < 0.7 &&
            "border-amber-500/50",
          credibility < 0.4 && "border-red-500/50"
        )}
      >
        <div
          className={cn(
            "w-2 h-2 rounded-full",
            credibility >= 0.7 && "bg-emerald-500",
            credibility >= 0.4 &&
              credibility < 0.7 &&
              "bg-amber-500",
            credibility < 0.4 && "bg-red-500"
          )}
        />
      </div>

      {/* Event card */}
      <div className="bg-card/50 backdrop-blur-sm border border-border rounded-lg p-4 hover:border-border/80 transition-colors">
        <div className="flex items-start justify-between gap-4 mb-2">
          <span className={credibilityClass}>
            {credibilityPercent}% credible
          </span>
          <time className="text-xs text-muted-foreground font-mono">
            {formatTimestamp(event.timestamp)}
          </time>
        </div>

        <p className="text-sm text-foreground leading-relaxed mb-3">
          {event.summary}
        </p>

        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          {event.location && (
            <span className="flex items-center gap-1">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
              {event.location}
            </span>
          )}
          {event.sources && event.sources.length > 0 && (
            <span className="flex items-center gap-1">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
              </svg>
              {formatSources(event.sources)}
              {event.sources.length > 3 && (
                <span>+{event.sources.length - 3} more</span>
              )}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
