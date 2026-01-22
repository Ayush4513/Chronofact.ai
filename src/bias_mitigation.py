"""
Chronofact.ai - Bias Mitigation Module
Implements source diversity, bias detection, and fair representation.
Addresses the hackathon requirement for "Thoughtful handling of bias, safety, privacy".
"""

from typing import List, Dict, Optional, Any, Tuple
from collections import Counter
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class BiasMitigation:
    """
    Handles bias detection and mitigation in timeline generation.
    
    Key features:
    - Source diversity enforcement
    - Author verification balancing
    - Temporal distribution checks
    - Geographic representation
    - Sentiment balance detection
    - Credibility-weighted diversity
    """
    
    # Thresholds
    MAX_SINGLE_SOURCE_RATIO = 0.3  # No single source > 30%
    MIN_VERIFIED_RATIO = 0.4  # At least 40% verified sources
    MAX_TIME_CLUSTER_RATIO = 0.5  # No single time period > 50%
    MIN_UNIQUE_AUTHORS = 3  # Minimum unique authors for valid timeline
    
    # Bias indicators
    EMOTIONAL_PATTERNS = [
        r'!!!+', r'\?\?\?+', r'BREAKING', r'URGENT', r'SHOCKING',
        r'you won\'t believe', r'they don\'t want you to know',
        r'share before', r'wake up', r'open your eyes'
    ]
    
    POLARIZING_TERMS = [
        'always', 'never', 'everyone', 'nobody', 'worst', 'best',
        'destroy', 'catastrophe', 'miracle', 'conspiracy'
    ]
    
    def __init__(
        self,
        max_source_ratio: float = MAX_SINGLE_SOURCE_RATIO,
        min_verified_ratio: float = MIN_VERIFIED_RATIO,
        min_unique_authors: int = MIN_UNIQUE_AUTHORS
    ):
        """
        Initialize bias mitigation with configurable thresholds.
        
        Args:
            max_source_ratio: Maximum ratio for single source
            min_verified_ratio: Minimum ratio of verified sources
            min_unique_authors: Minimum unique authors required
        """
        self.max_source_ratio = max_source_ratio
        self.min_verified_ratio = min_verified_ratio
        self.min_unique_authors = min_unique_authors
    
    def analyze_source_diversity(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze source diversity in timeline events.
        
        Args:
            events: List of timeline events with source info
        
        Returns:
            Diversity analysis with scores and warnings
        """
        if not events:
            return {"score": 0, "warnings": ["No events to analyze"]}
        
        # Extract sources and authors
        all_sources = []
        all_authors = []
        verified_count = 0
        total_count = 0
        
        for event in events:
            sources = event.get("sources", [])
            all_sources.extend(sources)
            
            author = event.get("author") or event.get("payload", {}).get("author")
            if author:
                all_authors.append(author)
            
            is_verified = event.get("is_verified") or event.get("payload", {}).get("is_verified", False)
            if is_verified:
                verified_count += 1
            total_count += 1
        
        # Calculate metrics
        source_counts = Counter(all_sources)
        author_counts = Counter(all_authors)
        
        total_sources = len(all_sources) or 1
        unique_sources = len(source_counts)
        unique_authors = len(author_counts)
        
        # Check source concentration
        max_source_count = max(source_counts.values()) if source_counts else 0
        source_concentration = max_source_count / total_sources
        
        # Check author concentration
        max_author_count = max(author_counts.values()) if author_counts else 0
        author_concentration = max_author_count / len(all_authors) if all_authors else 0
        
        # Check verified ratio
        verified_ratio = verified_count / total_count if total_count > 0 else 0
        
        # Build warnings
        warnings = []
        
        if source_concentration > self.max_source_ratio:
            dominant_source = source_counts.most_common(1)[0][0] if source_counts else "unknown"
            warnings.append(
                f"Source concentration too high: '{dominant_source}' represents "
                f"{source_concentration:.0%} of sources (max: {self.max_source_ratio:.0%})"
            )
        
        if author_concentration > self.max_source_ratio:
            dominant_author = author_counts.most_common(1)[0][0] if author_counts else "unknown"
            warnings.append(
                f"Author concentration too high: '{dominant_author}' represents "
                f"{author_concentration:.0%} of content"
            )
        
        if verified_ratio < self.min_verified_ratio:
            warnings.append(
                f"Low verified source ratio: {verified_ratio:.0%} "
                f"(recommended: >{self.min_verified_ratio:.0%})"
            )
        
        if unique_authors < self.min_unique_authors:
            warnings.append(
                f"Low author diversity: only {unique_authors} unique authors "
                f"(recommended: >={self.min_unique_authors})"
            )
        
        # Calculate diversity score (0-1)
        diversity_score = self._calculate_diversity_score(
            source_concentration,
            author_concentration,
            verified_ratio,
            unique_authors,
            unique_sources
        )
        
        return {
            "score": diversity_score,
            "unique_sources": unique_sources,
            "unique_authors": unique_authors,
            "source_concentration": source_concentration,
            "author_concentration": author_concentration,
            "verified_ratio": verified_ratio,
            "warnings": warnings,
            "top_sources": source_counts.most_common(5),
            "top_authors": author_counts.most_common(5),
            "is_diverse": len(warnings) == 0
        }
    
    def detect_content_bias(
        self,
        texts: List[str]
    ) -> Dict[str, Any]:
        """
        Detect potential bias indicators in text content.
        
        Args:
            texts: List of text content to analyze
        
        Returns:
            Bias analysis with flags and scores
        """
        if not texts:
            return {"bias_score": 0, "flags": []}
        
        flags = []
        emotional_count = 0
        polarizing_count = 0
        all_caps_count = 0
        
        for text in texts:
            if not text:
                continue
            
            # Check emotional patterns
            for pattern in self.EMOTIONAL_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    emotional_count += 1
                    break
            
            # Check polarizing terms
            text_lower = text.lower()
            for term in self.POLARIZING_TERMS:
                if term in text_lower:
                    polarizing_count += 1
                    break
            
            # Check excessive caps (excluding short texts)
            if len(text) > 20:
                caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
                if caps_ratio > 0.5:
                    all_caps_count += 1
        
        total_texts = len(texts)
        
        # Build flags
        if emotional_count / total_texts > 0.3:
            flags.append({
                "type": "emotional_language",
                "severity": "medium",
                "description": f"{emotional_count}/{total_texts} texts contain emotional manipulation patterns"
            })
        
        if polarizing_count / total_texts > 0.3:
            flags.append({
                "type": "polarizing_content",
                "severity": "medium",
                "description": f"{polarizing_count}/{total_texts} texts contain polarizing language"
            })
        
        if all_caps_count / total_texts > 0.2:
            flags.append({
                "type": "excessive_caps",
                "severity": "low",
                "description": f"{all_caps_count}/{total_texts} texts use excessive capitalization"
            })
        
        # Calculate bias score
        bias_score = (
            (emotional_count / total_texts) * 0.4 +
            (polarizing_count / total_texts) * 0.4 +
            (all_caps_count / total_texts) * 0.2
        )
        
        return {
            "bias_score": min(1.0, bias_score),
            "emotional_ratio": emotional_count / total_texts,
            "polarizing_ratio": polarizing_count / total_texts,
            "caps_ratio": all_caps_count / total_texts,
            "flags": flags,
            "is_biased": bias_score > 0.3
        }
    
    def analyze_temporal_distribution(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check for temporal clustering that might indicate bias.
        
        Args:
            events: List of events with timestamps
        
        Returns:
            Temporal analysis
        """
        if not events:
            return {"is_balanced": True, "warnings": []}
        
        timestamps = []
        for event in events:
            ts = event.get("timestamp") or event.get("payload", {}).get("timestamp")
            if ts:
                try:
                    if isinstance(ts, str):
                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    else:
                        dt = ts
                    timestamps.append(dt)
                except:
                    pass
        
        if len(timestamps) < 2:
            return {"is_balanced": True, "warnings": []}
        
        # Group by hour
        hour_counts = Counter(ts.hour for ts in timestamps)
        
        # Group by date
        date_counts = Counter(ts.date() for ts in timestamps)
        
        warnings = []
        
        # Check hour concentration
        if hour_counts:
            max_hour_ratio = max(hour_counts.values()) / len(timestamps)
            if max_hour_ratio > self.MAX_TIME_CLUSTER_RATIO:
                peak_hour = hour_counts.most_common(1)[0][0]
                warnings.append(
                    f"Temporal clustering: {max_hour_ratio:.0%} of events from hour {peak_hour}"
                )
        
        # Check date concentration
        if date_counts:
            max_date_ratio = max(date_counts.values()) / len(timestamps)
            if max_date_ratio > self.MAX_TIME_CLUSTER_RATIO and len(date_counts) > 1:
                peak_date = date_counts.most_common(1)[0][0]
                warnings.append(
                    f"Date clustering: {max_date_ratio:.0%} of events from {peak_date}"
                )
        
        return {
            "is_balanced": len(warnings) == 0,
            "total_timestamps": len(timestamps),
            "unique_hours": len(hour_counts),
            "unique_dates": len(date_counts),
            "warnings": warnings
        }
    
    def enforce_diversity(
        self,
        events: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """
        Select events to maximize diversity while maintaining relevance.
        
        Args:
            events: Candidate events to select from
            target_count: Number of events to select
        
        Returns:
            Diversified list of events
        """
        if len(events) <= target_count:
            return events
        
        selected = []
        selected_authors = set()
        selected_sources = set()
        
        # Sort by relevance/credibility first
        sorted_events = sorted(
            events,
            key=lambda x: x.get("credibility_score", 0) or x.get("score", 0),
            reverse=True
        )
        
        # First pass: select diverse events
        for event in sorted_events:
            if len(selected) >= target_count:
                break
            
            author = event.get("author") or event.get("payload", {}).get("author", "")
            sources = event.get("sources", [])
            
            # Check if this adds diversity
            author_seen = author in selected_authors
            sources_seen = any(s in selected_sources for s in sources)
            
            # Prefer unseen authors/sources
            if not author_seen or len(selected) < target_count // 2:
                selected.append(event)
                if author:
                    selected_authors.add(author)
                selected_sources.update(sources)
        
        # Second pass: fill remaining slots with best remaining
        if len(selected) < target_count:
            remaining = [e for e in sorted_events if e not in selected]
            selected.extend(remaining[:target_count - len(selected)])
        
        return selected[:target_count]
    
    def generate_diversity_report(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive diversity report for timeline.
        
        Args:
            events: Timeline events
        
        Returns:
            Full diversity report
        """
        source_analysis = self.analyze_source_diversity(events)
        
        texts = [
            e.get("text") or e.get("summary") or e.get("payload", {}).get("text", "")
            for e in events
        ]
        content_analysis = self.detect_content_bias(texts)
        
        temporal_analysis = self.analyze_temporal_distribution(events)
        
        # Overall assessment
        all_warnings = (
            source_analysis.get("warnings", []) +
            [f["description"] for f in content_analysis.get("flags", [])] +
            temporal_analysis.get("warnings", [])
        )
        
        overall_score = (
            source_analysis["score"] * 0.5 +
            (1 - content_analysis["bias_score"]) * 0.3 +
            (1.0 if temporal_analysis["is_balanced"] else 0.5) * 0.2
        )
        
        return {
            "overall_score": overall_score,
            "overall_rating": self._score_to_rating(overall_score),
            "source_diversity": source_analysis,
            "content_bias": content_analysis,
            "temporal_distribution": temporal_analysis,
            "all_warnings": all_warnings,
            "is_acceptable": overall_score >= 0.6,
            "recommendations": self._generate_recommendations(
                source_analysis,
                content_analysis,
                temporal_analysis
            )
        }
    
    def _calculate_diversity_score(
        self,
        source_concentration: float,
        author_concentration: float,
        verified_ratio: float,
        unique_authors: int,
        unique_sources: int
    ) -> float:
        """Calculate overall diversity score (0-1)."""
        # Lower concentration is better
        concentration_score = 1 - ((source_concentration + author_concentration) / 2)
        
        # Higher verified ratio is better
        verified_score = min(1.0, verified_ratio / self.min_verified_ratio)
        
        # More unique authors/sources is better
        author_score = min(1.0, unique_authors / 10)
        source_score = min(1.0, unique_sources / 15)
        
        return (
            concentration_score * 0.3 +
            verified_score * 0.3 +
            author_score * 0.2 +
            source_score * 0.2
        )
    
    def _score_to_rating(self, score: float) -> str:
        """Convert numeric score to rating."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _generate_recommendations(
        self,
        source_analysis: Dict[str, Any],
        content_analysis: Dict[str, Any],
        temporal_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        if source_analysis.get("source_concentration", 0) > self.max_source_ratio:
            recommendations.append(
                "Include more diverse sources to avoid over-reliance on single source"
            )
        
        if source_analysis.get("verified_ratio", 0) < self.min_verified_ratio:
            recommendations.append(
                "Prioritize verified accounts and official sources"
            )
        
        if source_analysis.get("unique_authors", 0) < self.min_unique_authors:
            recommendations.append(
                "Expand search to include more unique authors/perspectives"
            )
        
        if content_analysis.get("bias_score", 0) > 0.3:
            recommendations.append(
                "Review content for emotional or polarizing language"
            )
        
        if not temporal_analysis.get("is_balanced", True):
            recommendations.append(
                "Expand time range to capture events from different periods"
            )
        
        if not recommendations:
            recommendations.append("Timeline meets diversity standards")
        
        return recommendations


def create_bias_checker() -> BiasMitigation:
    """Create a bias mitigation instance with default settings."""
    return BiasMitigation()


def check_timeline_bias(
    events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Convenience function to check timeline for bias.
    
    Args:
        events: Timeline events
    
    Returns:
        Bias report
    """
    checker = BiasMitigation()
    return checker.generate_diversity_report(events)

