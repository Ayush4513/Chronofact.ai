import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { Timeline, MisinformationAnalysis, Recommendation, FollowUpQuestion } from "@/lib/api";
import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lightbulb,
  ExternalLink,
  ImagePlus,
  X,
  Upload,
  Zap,
  Shield,
  Clock,
  TrendingUp,
  Database,
  Cpu,
  Sparkles,
  Download,
  Share2,
  BookmarkPlus,
  Github,
  MapPin,
  Link2,
  ChevronDown,
  Activity,
} from "lucide-react";

// Animated Background Component
function ParticleBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-blue-950/50 to-purple-950/30" />
      
      {/* Animated gradient orbs */}
      <motion.div
        className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-blue-500/20 rounded-full blur-[120px]"
        animate={{
          x: [0, 100, 0],
          y: [0, 50, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-purple-500/20 rounded-full blur-[100px]"
        animate={{
          x: [0, -80, 0],
          y: [0, -60, 0],
          scale: [1, 1.1, 1],
        }}
        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[80px]"
        animate={{
          x: [0, 60, 0],
          y: [0, -40, 0],
        }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />
      
      {/* Grid pattern overlay */}
      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />
      
      {/* Floating particles */}
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-cyan-400/40 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -30, 0],
            opacity: [0.2, 0.8, 0.2],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            delay: Math.random() * 2,
          }}
        />
      ))}
    </div>
  );
}

// Credibility Meter Component
function CredibilityMeter({ score, size = "md" }: { score: number; size?: "sm" | "md" | "lg" }) {
  const percentage = Math.round(score * 100);
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score * circumference);
  
  const getColor = () => {
    if (score >= 0.7) return { stroke: "#10b981", bg: "rgba(16, 185, 129, 0.1)", text: "text-emerald-400" };
    if (score >= 0.4) return { stroke: "#f59e0b", bg: "rgba(245, 158, 11, 0.1)", text: "text-amber-400" };
    return { stroke: "#ef4444", bg: "rgba(239, 68, 68, 0.1)", text: "text-red-400" };
  };
  
  const color = getColor();
  const sizeClasses = {
    sm: "w-16 h-16",
    md: "w-24 h-24",
    lg: "w-32 h-32",
  };

  return (
    <div className={cn("relative", sizeClasses[size])}>
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="8"
        />
        <motion.circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={color.stroke}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          style={{ filter: `drop-shadow(0 0 6px ${color.stroke})` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span 
          className={cn("text-xl font-bold", color.text)}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
        >
          {percentage}%
        </motion.span>
        <span className="text-[10px] text-slate-400 uppercase tracking-wider">Credible</span>
      </div>
    </div>
  );
}

// Tech Badge Component
function TechBadge({ icon: Icon, label, color }: { icon: any; label: string; color: string }) {
  return (
    <motion.div
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-full border backdrop-blur-sm",
        "bg-white/5 border-white/10 hover:bg-white/10 transition-colors"
      )}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <Icon className={cn("h-3.5 w-3.5", color)} />
      <span className="text-xs font-medium text-slate-300">{label}</span>
    </motion.div>
  );
}

// Timeline Event Card Component
function TimelineEventCard({ 
  event, 
  index 
}: { 
  event: { 
    timestamp: string; 
    summary: string; 
    sources: string[]; 
    credibility_score: number; 
    location?: string;
  }; 
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const credibility = event.credibility_score || 0;
  const credibilityPercent = Math.round(credibility * 100);

  const getCredibilityStyle = () => {
    if (credibility >= 0.7) return { 
      border: "border-emerald-500/30", 
      glow: "shadow-emerald-500/10",
      badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      dot: "bg-emerald-500",
    };
    if (credibility >= 0.4) return { 
      border: "border-amber-500/30", 
      glow: "shadow-amber-500/10",
      badge: "bg-amber-500/20 text-amber-400 border-amber-500/30",
      dot: "bg-amber-500",
    };
    return { 
      border: "border-red-500/30", 
      glow: "shadow-red-500/10",
      badge: "bg-red-500/20 text-red-400 border-red-500/30",
      dot: "bg-red-500",
    };
  };

  const style = getCredibilityStyle();

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

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5 }}
      className="relative pl-8 pb-8 last:pb-0"
    >
      {/* Vertical line */}
      <div className="absolute left-[11px] top-8 bottom-0 w-px bg-gradient-to-b from-cyan-500/50 via-purple-500/30 to-transparent" />
      
      {/* Timeline node */}
      <motion.div
        className={cn(
          "absolute left-0 top-2 w-6 h-6 rounded-full border-2 flex items-center justify-center",
          "bg-slate-900 border-cyan-500/50"
        )}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: index * 0.1 + 0.2, type: "spring" }}
      >
        <div className={cn("w-2 h-2 rounded-full", style.dot)} />
      </motion.div>

      {/* Event card */}
      <motion.div
        className={cn(
          "relative overflow-hidden rounded-xl border backdrop-blur-md",
          "bg-white/5 hover:bg-white/10 transition-all duration-300",
          style.border,
          "shadow-xl", style.glow
        )}
        whileHover={{ scale: 1.01 }}
        layout
      >
        {/* Glow effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-transparent to-purple-500/5" />
        
        <div className="relative p-5">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex items-center gap-3">
              <span className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border",
                style.badge
              )}>
                <Shield className="h-3 w-3" />
                {credibilityPercent}%
              </span>
              {event.location && (
                <span className="flex items-center gap-1 text-xs text-slate-400">
                  <MapPin className="h-3 w-3" />
                  {event.location}
                </span>
              )}
            </div>
            <time className="text-xs text-slate-500 font-mono flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatTimestamp(event.timestamp)}
            </time>
          </div>

          {/* Summary */}
          <p className="text-sm text-slate-200 leading-relaxed mb-4">
            {event.summary}
          </p>

          {/* Sources */}
          {event.sources && event.sources.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Link2 className="h-3 w-3" />
                Sources:
              </span>
              {event.sources.slice(0, 3).map((source, i) => (
                <a
                  key={i}
                  href={`https://x.com/i/web/status/${source}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors font-mono"
                >
                  #{source.slice(-6)}
                </a>
              ))}
              {event.sources.length > 3 && (
                <span className="text-xs text-slate-500">+{event.sources.length - 3} more</span>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

// Follow Up Questions Component
function FollowUpQuestionsPanel({
  questions,
  loading,
  error,
  onQuestionClick,
}: {
  questions: FollowUpQuestion[];
  loading: boolean;
  error?: string | null;
  onQuestionClick: (question: string) => void;
}) {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'deep_dive': return <Search className="h-3.5 w-3.5" />;
      case 'related_topic': return <TrendingUp className="h-3.5 w-3.5" />;
      case 'verification': return <Shield className="h-3.5 w-3.5" />;
      case 'prediction': return <Sparkles className="h-3.5 w-3.5" />;
      case 'comparison': return <Activity className="h-3.5 w-3.5" />;
      default: return <Lightbulb className="h-3.5 w-3.5" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'deep_dive': return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';
      case 'related_topic': return 'text-purple-400 bg-purple-500/10 border-purple-500/30';
      case 'verification': return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      case 'prediction': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
      case 'comparison': return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'deep_dive': return 'Deep Dive';
      case 'related_topic': return 'Related';
      case 'verification': return 'Verify';
      case 'prediction': return 'Predict';
      case 'comparison': return 'Compare';
      default: return category;
    }
  };

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-white/10 bg-slate-900/50 backdrop-blur-md p-6"
      >
        <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Lightbulb className="h-4 w-4" />
          Generating Questions...
        </h4>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-white/5 rounded w-3/4 mb-2" />
              <div className="h-3 bg-white/5 rounded w-1/2" />
            </div>
          ))}
        </div>
      </motion.div>
    );
  }

  // Show error state
  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-red-500/20 bg-slate-900/50 backdrop-blur-md p-6"
      >
        <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-red-400" />
          Follow-Up Questions
        </h4>
        <p className="text-xs text-red-400 flex items-center gap-2">
          <XCircle className="h-3.5 w-3.5" />
          {error}
        </p>
      </motion.div>
    );
  }

  // Show empty state with message instead of hiding
  if (questions.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-xl border border-white/10 bg-slate-900/50 backdrop-blur-md p-6"
      >
        <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-amber-400" />
          Continue Exploring
        </h4>
        <p className="text-xs text-slate-500">
          No follow-up questions available for this query. Try a different topic!
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 }}
      className="rounded-xl border border-white/10 bg-slate-900/50 backdrop-blur-md p-6"
    >
      <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
        <Lightbulb className="h-4 w-4 text-amber-400" />
        Continue Exploring
      </h4>
      <p className="text-xs text-slate-500 mb-4">
        Click a question to dig deeper
      </p>
      <div className="space-y-3">
        {questions.slice(0, 5).map((q, i) => (
          <motion.button
            key={i}
            onClick={() => onQuestionClick(q.question)}
            className="w-full text-left group"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
          >
            <div className="p-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 hover:border-cyan-500/30 transition-all">
              <div className="flex items-start gap-3">
                <div className={cn(
                  "flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center border",
                  getCategoryColor(q.category)
                )}>
                  {getCategoryIcon(q.category)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white group-hover:text-cyan-300 transition-colors leading-snug">
                    {q.question}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded-full uppercase tracking-wider border",
                      getCategoryColor(q.category)
                    )}>
                      {getCategoryLabel(q.category)}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {q.context_hint}
                    </span>
                  </div>
                </div>
                <ChevronDown className="h-4 w-4 text-slate-500 group-hover:text-cyan-400 transition-colors transform -rotate-90" />
              </div>
            </div>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

// Loading State Component
function LoadingState({ hasImage = false }: { hasImage?: boolean }) {
  const steps = hasImage 
    ? ["Processing Image", "Extracting Context", "Searching", "Verifying"]
    : ["Searching", "Analyzing", "Verifying"];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center py-20"
    >
      <div className="relative">
        {/* Outer ring */}
        <motion.div
          className="w-24 h-24 rounded-full border-2 border-cyan-500/30"
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
        />
        {/* Inner ring */}
        <motion.div
          className="absolute inset-2 rounded-full border-2 border-purple-500/30"
          animate={{ rotate: -360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        />
        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1, repeat: Infinity }}
          >
            {hasImage ? (
              <ImagePlus className="h-8 w-8 text-purple-400" />
            ) : (
              <Cpu className="h-8 w-8 text-cyan-400" />
            )}
          </motion.div>
        </div>
      </div>
      
      <motion.div
        className="mt-8 text-center"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h3 className="text-xl font-bold text-white mb-2">
          {hasImage ? "Analyzing Image & Building Timeline" : "Building Timeline"}
        </h3>
        <p className="text-sm text-slate-400 max-w-xs">
          {hasImage 
            ? "Processing visual context with Gemini AI, then building your verified timeline..."
            : "Analyzing sources, cross-referencing facts, and building your verified timeline..."
          }
        </p>
      </motion.div>
      
      {/* Progress indicators */}
      <div className="flex items-center gap-4 mt-6 flex-wrap justify-center">
        {steps.map((step, i) => (
          <motion.div
            key={step}
            className="flex items-center gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.5 }}
          >
            <motion.div
              className={cn(
                "w-2 h-2 rounded-full",
                hasImage && i < 2 ? "bg-purple-500" : "bg-cyan-500"
              )}
              animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1, repeat: Infinity, delay: i * 0.3 }}
            />
            <span className="text-xs text-slate-400">{step}</span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

// Main App Component
export function App() {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(10);
  const [loading, setLoading] = useState(false);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [detectResult, setDetectResult] = useState<MisinformationAnalysis | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [apiStatus, setApiStatus] = useState<"checking" | "connected" | "disconnected">("checking");
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [followUpQuestions, setFollowUpQuestions] = useState<FollowUpQuestion[]>([]);
  const [questionHistory, setQuestionHistory] = useState<string[]>([]);
  const [loadingFollowUp, setLoadingFollowUp] = useState(false);
  const [followUpError, setFollowUpError] = useState<string | null>(null);

  useEffect(() => {
    checkApiStatus();
    // Force dark mode
    document.documentElement.classList.add("dark");
  }, []);

  const checkApiStatus = async () => {
    try {
      const health = await api.healthCheck();
      setApiStatus(health.qdrant_connected && health.baml_available ? "connected" : "disconnected");
    } catch {
      setApiStatus("disconnected");
    }
  };

  const handleSearch = async (searchQuery?: string) => {
    const queryToUse = searchQuery || query;
    
    // Allow search if there's text OR an image
    if (!queryToUse.trim() && !selectedImage) return;
    
    // Update query if using a follow-up question
    if (searchQuery) {
      setQuery(searchQuery);
      setQuestionHistory(prev => [...prev, searchQuery]);
    }
    
    setLoading(true);
    setError(null);
    setDetectResult(null);
    setRecommendations([]);
    setFollowUpQuestions([]);
    setFollowUpError(null);

    try {
      // Use default topic if only image provided
      const effectiveTopic = queryToUse.trim() || "Analyze uploaded image";
      
      // Prepare request with optional image
      const request: { topic: string; limit: number; image_base64?: string } = {
        topic: effectiveTopic,
        limit,
      };

      // Convert image to base64 if present
      if (selectedImage && imagePreview) {
        // Extract base64 data from data URL (remove "data:image/...;base64," prefix)
        const base64Data = imagePreview.split(",")[1];
        if (base64Data) {
          request.image_base64 = base64Data;
        }
      }

      const result = await api.generateTimeline(request);
      setTimeline(result);
      if (result.events && result.events.length > 0) {
        await runAnalysis(effectiveTopic);
        // Generate follow-up questions after timeline is ready
        await fetchFollowUpQuestions(effectiveTopic, result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate timeline");
      setTimeline(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchFollowUpQuestions = async (searchQuery: string, timelineResult: Timeline) => {
    setLoadingFollowUp(true);
    setFollowUpError(null);
    try {
      console.log("Fetching follow-up questions for:", searchQuery);
      const response = await api.getFollowUpQuestions({
        original_query: searchQuery,
        timeline_topic: timelineResult.topic,
        events_summary: timelineResult.events?.map(e => e.summary) || [],
        avg_credibility: timelineResult.avg_credibility || 0.5,
        total_events: timelineResult.events?.length || 0,
        total_sources: timelineResult.total_sources || 0,
        previous_questions: questionHistory,
      });
      console.log("Follow-up questions response:", response);
      setFollowUpQuestions(response.questions || []);
      if (!response.questions || response.questions.length === 0) {
        console.warn("No follow-up questions returned from API");
      }
    } catch (err) {
      console.error("Failed to fetch follow-up questions:", err);
      setFollowUpError(err instanceof Error ? err.message : "Failed to load questions");
    } finally {
      setLoadingFollowUp(false);
    }
  };

  const handleFollowUpClick = (question: string) => {
    handleSearch(question);
  };

  const runAnalysis = async (searchQuery: string) => {
    try {
      const [detectResult, recommendationsResult] = await Promise.all([
        api.detectMisinformation({ text: searchQuery }),
        api.getRecommendations({ query: searchQuery, limit: 5 }),
      ]);
      setDetectResult(detectResult);
      setRecommendations(recommendationsResult.recommendations || []);
    } catch (err) {
      console.warn("Analysis error:", err);
    }
  };

  const handleImageSelect = (file: File) => {
    if (file && file.type.startsWith("image/")) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setImagePreview(e.target?.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleImageDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleImageSelect(file);
  };

  const removeImage = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setSelectedImage(null);
    setImagePreview(null);
  };

  const exampleQueries = [
    "Mumbai elections 2024",
    "Silicon Valley tech layoffs",
    "Climate summit outcomes",
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-x-hidden">
      <ParticleBackground />
      
      {/* Header */}
      <motion.header 
        className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl"
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <motion.div 
                className="relative w-10 h-10"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500 to-purple-600 rounded-xl blur-sm opacity-80" />
                <div className="relative w-full h-full bg-gradient-to-br from-cyan-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Zap className="h-5 w-5 text-white" />
                </div>
              </motion.div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">
                  <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
                    Chronofact.ai
                  </span>
                </h1>
                <p className="text-[10px] text-slate-500 uppercase tracking-widest">
                  AI Timeline Generator
                </p>
              </div>
            </div>

            {/* Status */}
            <div className="flex items-center gap-4">
              <motion.div 
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10"
                animate={apiStatus === "checking" ? { opacity: [0.5, 1, 0.5] } : {}}
                transition={{ duration: 1, repeat: apiStatus === "checking" ? Infinity : 0 }}
              >
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  apiStatus === "connected" && "bg-emerald-500 shadow-lg shadow-emerald-500/50",
                  apiStatus === "disconnected" && "bg-red-500 shadow-lg shadow-red-500/50",
                  apiStatus === "checking" && "bg-amber-500 animate-pulse"
                )} />
                <span className="text-xs text-slate-400">
                  {apiStatus === "connected" ? "System Online" : apiStatus === "disconnected" ? "Offline" : "Connecting..."}
                </span>
              </motion.div>
            </div>
          </div>
        </div>
      </motion.header>

      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <motion.section 
          className="text-center py-12 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* Tech badges */}
          <motion.div 
            className="flex flex-wrap items-center justify-center gap-3 mb-8"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <TechBadge icon={Database} label="Qdrant Vector DB" color="text-cyan-400" />
            <TechBadge icon={Cpu} label="BAML Structured AI" color="text-purple-400" />
            <TechBadge icon={Sparkles} label="Gemini AI" color="text-amber-400" />
          </motion.div>

          {/* Main headline */}
          <motion.h2 
            className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500 bg-clip-text text-transparent">
              Discover Truth
            </span>
            <br />
            <span className="text-white">Through Time</span>
          </motion.h2>

          <motion.p 
            className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            Build accurate, verifiable event timelines with AI-powered fact-checking 
            and real-time credibility assessment
          </motion.p>
        </motion.section>

        {/* Search Card */}
        <motion.section 
          className="max-w-4xl mx-auto mb-12"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <div className="relative">
            {/* Glow effect */}
            <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-cyan-500/20 rounded-2xl blur-xl" />
            
            <div className="relative rounded-2xl border border-white/10 bg-slate-900/80 backdrop-blur-xl p-6 shadow-2xl">
              {/* Search input row */}
              <div className="flex flex-col md:flex-row gap-4 mb-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
                  <input
                    type="text"
                    placeholder="e.g., 'Mumbai elections 2024', 'Silicon Valley tech layoffs'"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (query.trim() || selectedImage) && handleSearch(undefined)}
                    className="w-full pl-12 pr-4 py-4 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all"
                  />
                </div>
                <div className="flex gap-3">
                  <input
                    type="number"
                    min={3}
                    max={50}
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="w-20 px-4 py-4 rounded-xl bg-white/5 border border-white/10 text-white text-center focus:outline-none focus:border-cyan-500/50 transition-all"
                  />
                  <motion.button
                    type="button"
                    onClick={() => handleSearch(undefined)}
                    disabled={loading || (!query.trim() && !selectedImage)}
                    className={cn(
                      "px-6 py-4 rounded-xl font-semibold flex items-center gap-2 transition-all",
                      "bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500",
                      "text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40",
                      "disabled:opacity-50 disabled:cursor-not-allowed"
                    )}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-5 w-5 animate-spin" />
                        <span className="hidden md:inline">Generating...</span>
                      </>
                    ) : (
                      <>
                        <Zap className="h-5 w-5" />
                        <span className="hidden md:inline">{selectedImage && !query.trim() ? "Analyze Image" : "Generate Timeline"}</span>
                      </>
                    )}
                  </motion.button>
                </div>
              </div>

              {/* Example queries */}
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="text-xs text-slate-500">Try:</span>
                {exampleQueries.map((q) => (
                  <button
                    key={q}
                    onClick={() => setQuery(q)}
                    className="text-xs px-3 py-1 rounded-full bg-white/5 border border-white/10 text-slate-400 hover:text-cyan-400 hover:border-cyan-500/30 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Image upload */}
              <div className="border-t border-white/10 pt-4">
                <p className="text-xs text-slate-500 mb-3 flex items-center gap-2">
                  <ImagePlus className="h-3.5 w-3.5" />
                  Attach Image for Visual Context
                  <span className="text-cyan-400/60">(AI will analyze the image)</span>
                </p>
                
                {!imagePreview ? (
                  <div
                    className={cn(
                      "border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all",
                      isDragging
                        ? "border-cyan-500/50 bg-cyan-500/10"
                        : "border-white/10 hover:border-white/20 bg-white/5"
                    )}
                    onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleImageDrop}
                    onClick={() => document.getElementById("image-input")?.click()}
                  >
                    <input
                      id="image-input"
                      type="file"
                      accept="image/*"
                      onChange={(e) => e.target.files?.[0] && handleImageSelect(e.target.files[0])}
                      className="hidden"
                    />
                    <Upload className="h-8 w-8 text-slate-500 mx-auto mb-2" />
                    <p className="text-sm text-slate-400">Drop image or click to upload</p>
                    <p className="text-xs text-slate-600 mt-1">Image will be analyzed by Gemini AI to enhance timeline context</p>
                  </div>
                ) : (
                  <div className="flex items-start gap-4">
                    <div className="relative">
                      <img src={imagePreview} alt="Selected" className="max-h-32 rounded-lg border border-white/10" />
                      <button
                        type="button"
                        onClick={removeImage}
                        className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 text-xs text-emerald-400 mb-1">
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Image ready for analysis
                      </div>
                      <p className="text-xs text-slate-500">
                        {selectedImage?.name} ({((selectedImage?.size || 0) / 1024).toFixed(1)} KB)
                      </p>
                      <p className="text-xs text-slate-600 mt-2">
                        The image will be analyzed to extract visual context for your timeline query
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.section>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="max-w-4xl mx-auto mb-8"
            >
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-3">
                <XCircle className="h-5 w-5 text-red-400" />
                <span className="text-red-400">{error}</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Timeline Section */}
          <div className="lg:col-span-2">
            <AnimatePresence mode="wait">
              {loading ? (
                <LoadingState key="loading" hasImage={!!selectedImage} />
              ) : timeline ? (
                <motion.div
                  key="timeline"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  {/* Timeline header */}
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2">{timeline.topic}</h3>
                      <div className="flex items-center gap-4">
                        <span className="flex items-center gap-2 text-sm text-slate-400">
                          <Activity className="h-4 w-4 text-cyan-400" />
                          {timeline.events?.length || 0} Events
                        </span>
                        <span className="flex items-center gap-2 text-sm text-slate-400">
                          <TrendingUp className="h-4 w-4 text-purple-400" />
                          {Math.round((timeline.avg_credibility || 0) * 100)}% Avg Credibility
                        </span>
                      </div>
                    </div>
                    
                    {/* Action buttons */}
                    <div className="flex items-center gap-2">
                      <motion.button 
                        className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <Download className="h-4 w-4" />
                      </motion.button>
                      <motion.button 
                        className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <Share2 className="h-4 w-4" />
                      </motion.button>
                      <motion.button 
                        className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <BookmarkPlus className="h-4 w-4" />
                      </motion.button>
                    </div>
                  </div>

                  {/* Timeline events */}
                  <div className="relative">
                    {timeline.events?.map((event, index) => (
                      <TimelineEventCard key={index} event={event} index={index} />
                    ))}
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center py-20 text-center"
                >
                  <motion.div
                    className="w-24 h-24 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center mb-6 border border-white/10"
                    animate={{ rotate: [0, 5, -5, 0] }}
                    transition={{ duration: 4, repeat: Infinity }}
                  >
                    <Search className="h-10 w-10 text-cyan-400" />
                  </motion.div>
                  <h3 className="text-xl font-bold text-white mb-2">Ready to Investigate?</h3>
                  <p className="text-slate-400 max-w-md">
                    Enter a topic above to generate a fact-checked, AI-verified timeline of events
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Credibility Overview */}
            {timeline && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="rounded-xl border border-white/10 bg-slate-900/50 backdrop-blur-md p-6"
              >
                <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                  Credibility Score
                </h4>
                <div className="flex justify-center mb-4">
                  <CredibilityMeter score={timeline.avg_credibility || 0} size="lg" />
                </div>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-white">{timeline.events?.length || 0}</p>
                    <p className="text-xs text-slate-500">Events</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-white">{timeline.total_sources || 0}</p>
                    <p className="text-xs text-slate-500">Sources</p>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Misinformation Detection */}
            {detectResult && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                className="rounded-xl border border-white/10 bg-slate-900/50 backdrop-blur-md p-6"
              >
                <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Risk Analysis
                </h4>
                <div className={cn(
                  "inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold mb-4",
                  detectResult.risk_level?.toLowerCase() === "low" && "bg-emerald-500/20 text-emerald-400",
                  detectResult.risk_level?.toLowerCase() === "medium" && "bg-amber-500/20 text-amber-400",
                  detectResult.risk_level?.toLowerCase() === "high" && "bg-red-500/20 text-red-400"
                )}>
                  {detectResult.risk_level || "Unknown"} Risk
                </div>
                {detectResult.suspicious_patterns && detectResult.suspicious_patterns.length > 0 && (
                  <div className="space-y-2">
                    {detectResult.suspicious_patterns.map((pattern, i) => (
                      <p key={i} className="text-xs text-slate-400 flex items-start gap-2">
                        <span className="text-amber-500">•</span>
                        {pattern}
                      </p>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {/* Follow-Up Questions - Always show when timeline exists */}
            {timeline && (
              <FollowUpQuestionsPanel
                questions={followUpQuestions}
                loading={loadingFollowUp}
                error={followUpError}
                onQuestionClick={handleFollowUpClick}
              />
            )}

            {/* Recommendations */}
            {recommendations.length > 0 && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
                className="rounded-xl border border-white/10 bg-slate-900/50 backdrop-blur-md p-6"
              >
                <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                  <Lightbulb className="h-4 w-4" />
                  Suggestions
                </h4>
                <div className="space-y-2">
                  {recommendations.slice(0, 3).map((rec, i) => (
                    <button
                      key={i}
                      onClick={() => handleFollowUpClick(rec.action)}
                      className="w-full text-left p-3 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 hover:border-cyan-500/30 transition-all"
                    >
                      <p className="text-sm text-white mb-1">{rec.action}</p>
                      <p className="text-xs text-slate-500">{rec.reason}</p>
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* System Status */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="rounded-xl border border-white/10 bg-slate-900/50 backdrop-blur-md p-6"
            >
              <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
                System Status
              </h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">API</span>
                  <span className={cn(
                    "flex items-center gap-2 text-sm",
                    apiStatus === "connected" ? "text-emerald-400" : "text-red-400"
                  )}>
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      apiStatus === "connected" ? "bg-emerald-500" : "bg-red-500"
                    )} />
                    {apiStatus === "connected" ? "Online" : "Offline"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Vector DB</span>
                  <span className="flex items-center gap-2 text-sm text-emerald-400">
                    <div className="w-2 h-2 rounded-full bg-emerald-500" />
                    Qdrant
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">AI Model</span>
                  <span className="flex items-center gap-2 text-sm text-purple-400">
                    <div className="w-2 h-2 rounded-full bg-purple-500" />
                    Gemini
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 mt-20 py-8 bg-slate-950/80 backdrop-blur-xl">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-cyan-400" />
                <span className="font-semibold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                  Chronofact.ai
                </span>
              </div>
              <div className="h-4 w-px bg-white/20" />
              <span className="text-sm text-slate-500">
                Built for <span className="text-cyan-400">Qdrant Convolve 4.0</span>
              </span>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-xs text-slate-500">Deployed on Render</span>
              <a
                href="https://github.com/Ayush4513/Chronofact.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-sm text-slate-300"
              >
                <Github className="h-4 w-4" />
                View on GitHub
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
