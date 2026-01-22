class Event {
  timestamp string @description("ISO 8601 format timestamp of when event occurred")
  summary string @description("Brief description of event")
  sources string[] @description("List of X post IDs or URLs as sources for this event")
  media string? @description("Optional image or video URL associated with event")
  credibility_score float @description("0.0 to 1.0, higher is more credible")
  verified_sources int @description("Number of sources verified against knowledge base")
}

class Timeline {
  topic string @description("The topic or query this timeline addresses")
  events Event[] @description("Chronological list of events")
  total_sources int @description("Total number of unique sources across all events")
  avg_credibility float @description("Average credibility score across all events")
  predictions string[]? @description("Optional what-if predictions based on observed patterns")
}

class KnowledgeFact {
  fact_id string @description("Unique identifier for this fact")
  statement string @description("The factual statement")
  sources string[] @description("Sources that verify this fact")
  verification_status string @description("One of: 'verified', 'disputed', or 'unverified'")
  verified_at string @description("ISO timestamp when this fact was verified")
}

class Recommendation {
  action string @description("Suggested action or follow-up query")
  reason string @description("Why this recommendation is being made")
}

class SessionMemory {
  session_id string @description("Unique session identifier")
  query string @description("The query that was made")
  timestamp string @description("ISO timestamp of when query was made")
  results_count int @description("Number of results returned for query")
  relevance_score float @description("Relevance score of results (0.0 to 1.0)")
}

class XPost {
  tweet_id string @description("Unique X post identifier")
  text string @description("Content of post")
  author string @description("Username of author")
  timestamp string @description("ISO timestamp when post was created")
  fave_count int @description("Number of favorites/likes")
  retweet_count int @description("Number of retweets")
  is_verified bool @description("Whether author is verified")
  media_urls string[] @description("List of media URLs (images, videos)")
  location string? @description("Optional location tag")
  credibility_score float @description("Calculated credibility score (0.0 to 1.0)")
}

class ProcessedQuery {
  original_query string @description("The original user query")
  rewritten_query string @description("Optimized query for searching")
  entities string[] @description("Extracted entities from query")
  time_range string? @description("Inferred time range if any")
}

class CredibilityAssessment {
  post_id string @description("ID of the post being assessed")
  credibility_score float @description("Overall credibility score (0.0 to 1.0)")
  factors string[] @description("Factors that influenced the score")
  reasoning string @description("Explanation for the assigned score")
}

class MisinformationAnalysis {
  is_suspicious bool
  suspicious_patterns string[]
  risk_level string @description("low, medium, or high")
  recommendation string
}

function GenerateTimeline(query: string, retrieved_context: string, num_events: int) -> Timeline {
  client GeminiFlash
  prompt #"
    You are building a factual, chronological timeline for topic: {{ query }}

    Below is retrieved context from verified X posts and knowledge base:

    {{ retrieved_context }}

    Generate a timeline with exactly {{ num_events }} events following these strict rules:

    1. CHRONOLOGICAL ORDER: Events must be in strict chronological order (earliest first)
    2. SOURCE CITATION: Each event must cite specific sources (X post IDs or URLs)
    3. CREDIBILITY SCORES: Assign credibility scores based on:
       - Source verification status
       - Author verification
       - Engagement quality (meaningful interactions, not just spam)
       - Consistency with known facts
    4. ACCURACY: Be accurate and ground everything in provided context
    5. NO HALLUCINATION: Do not invent facts. Only use information from context
    6. UNCERTAINTY HANDLING: If information is uncertain, mark credibility score low
    7. PREDICTIONS (Optional): Generate 2-3 what-if predictions based on observed patterns

    Return as a Timeline object with all required fields:
    - topic: The main topic of this timeline
    - events: Array of Event objects (each with timestamp, summary, sources, credibility_score, etc.)
    - total_sources: Total unique sources across all events
    - avg_credibility: Average credibility across all events (0.0 to 1.0)
    - predictions: Optional array of predictions based on patterns

    Format your response as valid JSON that matches the Timeline schema.
  "#
}

function ProcessQuery(original_query: string, context: string?) -> ProcessedQuery {
  client GeminiFlash
  prompt #"
    The user asked: {{ original_query }}

    {% if context %}
    Previous context: {{ context }}
    {% endif %}

    Rewrite this query to be more precise for searching X posts and knowledge base.
    Focus on:
    1. Specific entities (people, organizations, locations, events)
    2. Time ranges if implied
    3. Key themes or topics
    4. Disambiguation (e.g., which "Mumbai" - city, district, etc.)

    The rewritten query should be optimized for:
    - Vector similarity search
    - Keyword matching
    - Metadata filtering

    Extract the main entities mentioned.
    Identify any implicit time ranges.

    Return as a ProcessedQuery object with:
    - original_query: The original query as provided
    - rewritten_query: The optimized query
    - entities: Array of key entities extracted
    - time_range: Optional inferred time range if mentioned

    Return only the object, nothing else.
  "#
}

function ExtractEntities(text: string) -> string[] {
  client GeminiFlash
  prompt #"
    Extract key entities from this text:

    {{ text }}

    Entities can be:
    - People (names, roles)
    - Organizations
    - Locations (cities, regions, countries)
    - Events (specific incidents, announcements)
    - Dates and times
    - Topics or themes

    Return as an array of entity names, most important first (max 10 entities).
    Only return the entity names, nothing else.
  "#
}

function AssessCredibility(post_text: string, author_info: string, engagement: string, knowledge_context: string?) -> CredibilityAssessment {
  client GeminiFlash
  prompt #"
    Assess the credibility of this X post:

    POST CONTENT:
    {{ post_text }}

    AUTHOR INFO:
    {{ author_info }}

    ENGAGEMENT METRICS:
    {{ engagement }}

    {% if knowledge_context %}
    CONTEXT FROM VERIFIED KNOWLEDGE BASE:
    {{ knowledge_context }}
    {% endif %}

    Consider these factors when assessing credibility:

    1. AUTHOR VERIFICATION:
       - Is the author verified?
       - Does the author have a history of credible posts?
       - Is the author affiliated with a reputable organization?

    2. CONTENT QUALITY:
       - Does the content make factual claims or opinions?
       - Is it specific with verifiable details (times, locations, names)?
       - Does it cite sources or provide evidence?

    3. ENGAGEMENT QUALITY:
       - Is engagement organic or suspicious (botted)?
       - Are comments/replies constructive or spammy?
       - High-quality engagement from credible users increases credibility

    4. CONSISTENCY:
       - Is it consistent with known facts?
       - Does it contradict verified information?
       - Does it align with multiple independent sources?

    5. RECENCY AND RELEVANCE:
       - Is the content recent and relevant to current events?
       - Is it being reported by multiple sources?

    6. RED FLAGS (lower credibility):
       - Excessive use of all-caps or emojis
       - Conspiracy theories without evidence
       - Clickbait language
       - Anonymous or new accounts
       - Overly emotional or sensational language

    Assign a credibility score (0.0 to 1.0) where:
    - 0.8 - 1.0: Highly credible (verified, well-sourced, consistent)
    - 0.5 - 0.8: Moderately credible (some verification, reasonable)
    - 0.2 - 0.5: Low credibility (unverified, some red flags)
    - 0.0 - 0.2: Not credible (major red flags, contradictory)

    Return as a CredibilityAssessment object with:
    - post_id: Identifier for the post
    - credibility_score: Float between 0.0 and 1.0
    - factors: Array of key factors that influenced the score
    - reasoning: Explanation for the assigned score
  "#
}

function DetectMisinformation(text: string) -> MisinformationAnalysis {
  client GeminiFlash
  prompt #"
    Analyze this text for potential misinformation patterns:

    {{ text }}

    Look for these suspicious patterns:

    1. EMOTIONAL MANIPULATION:
       - Exaggerated emotional language
       - Fear-mongering
       - Urgency ("share this now!")

    2. MISLEADING HEADLINES:
       - Clickbait titles
       - Missing critical context
       - Out-of-context quotes

    3. SOURCE ISSUES:
       - Anonymous claims without attribution
       - "Sources say" without specifying
       - Citing unreliable sources

    4. FACTUAL INACCURACIES:
       - Inconsistent timestamps
       - Impossible claims
       - Contradicts basic facts

    5. NARRATIVE PATTERNS:
       - Conspiracy theories
       - "They don't want you to know" framing
       - Over-simplification of complex issues

    Assess risk level:
    - LOW: No obvious red flags, minor issues
    - MEDIUM: Some concerning patterns, verify before sharing
    - HIGH: Multiple red flags, likely misinformation

    Return as JSON with:
    - is_suspicious: Boolean
    - suspicious_patterns: Array of detected patterns
    - risk_level: One of "low", "medium", or "high"
    - recommendation: Action to take (verify, ignore, report, etc.)
  "#
}

function GenerateRecommendations(query: string, timeline: Timeline?, user_session: SessionMemory[]?) -> Recommendation[] {
  client GeminiFlash
  prompt #"
    Given this query and timeline:

    QUERY: {{ query }}

    {% if timeline %}
    TIMELINE SUMMARY:
    Topic: {{ timeline.topic }}
    Events: {{ timeline.events.length }}
    Avg Credibility: {{ timeline.avg_credibility }}
    Sources: {{ timeline.total_sources }}
    {% endif %}

    {% if user_session %}
    USER'S RECENT QUERIES:
    {% for mem in user_session %}
    - {{ mem.query }} (relevance: {{ mem.relevance_score }})
    {% endfor %}
    {% endif %}

    Generate 3-5 context-aware recommendations for follow-up actions.
    Consider:

    1. DEEP DIVE OPPORTUNITIES:
       - Are there events that need more investigation?
       - Are there gaps in the timeline?
       - Are there unverified claims to explore?

    2. RELATED TOPICS:
       - What related events or topics might the user be interested in?
       - What happened before/after this timeline?
       - What related locations or people are involved?

    3. FACT-CHECKING SUGGESTIONS:
       - Are there claims that should be verified against official sources?
       - Are there contradictory accounts that need reconciliation?

    4. PREDICTIVE INSIGHTS:
       - Based on patterns, what might happen next?
       - What should the user watch for?

    5. USER INTEREST ALIGNMENT:
       - Based on their recent queries, what else might interest them?

    Return as an array of Recommendation objects, each with:
    - action: Specific action or follow-up query
    - reason: Why this is being recommended
  "#
}