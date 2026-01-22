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
      className="relative pl-10 pb-8 last:pb-0"
      style={{ animationDelay: `${index * 100}ms` }}
    >
      {/* Timeline line with gradient */}
      <div className="absolute left-[13.5px] top-7 bottom-0 w-0.5 bg-gradient-to-b from-blue-400/30 via-purple-400/30 to-transparent" />

      {/* Timeline dot */}
      <div
        className={cn(
          "absolute left-0 top-1.5 w-7 h-7 rounded-full border-2 bg-white dark:bg-slate-900 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform",
          credibility >= 0.7 && "border-emerald-500/60 shadow-emerald-500/20",
          credibility >= 0.4 &&
            credibility < 0.7 &&
            "border-amber-500/60 shadow-amber-500/20",
          credibility < 0.4 && "border-red-500/60 shadow-red-500/20"
        )}
      >
        <div
          className={cn(
            "w-3 h-3 rounded-full ring-2 ring-white dark:ring-slate-900",
            credibility >= 0.7 && "bg-emerald-500",
            credibility >= 0.4 &&
              credibility < 0.7 &&
              "bg-amber-500",
            credibility < 0.4 && "bg-red-500"
          )}
        />
      </div>

      {/* Event card */}
      <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border border-border/50 rounded-xl p-5 hover:border-blue-300/50 dark:hover:border-blue-700/50 hover:shadow-lg transition-all duration-300 group">
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
