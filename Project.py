"""Lightweight in-memory content discovery toolkit.

The module provides simple data classes that model learning content and user
profiles together with an in-memory vector database that supports lexical and
hybrid retrieval strategies.  It deliberately avoids third-party dependencies
so the code can run in restricted execution environments such as this kata.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Set
import json
import hashlib
import re
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from collections import defaultdict

import math
import string

@dataclass
class LearningContent:
    """Represents an item that can be recommended to a learner."""

    id: str
    title: str
    content_type: str
    source: str
    url: str
    description: str
    difficulty: str
    duration_minutes: int
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    checksum: Optional[str] = None

    def document_text(self) -> str:
        """Concatenate searchable fields into a single string."""

        parts: List[str] = [self.title, self.description]
        parts.extend(self.tags)
        parts.extend(self.prerequisites)
        for key, value in self.metadata.items():
            parts.append(f"{key}: {value}")
        return " ".join(part for part in parts if part)

@dataclass
class UserProfile:
    """Small representation of a learner used for personalization."""

    user_id: str
    knowledge_areas: Dict[str, str] = field(default_factory=dict)
    learning_goals: List[str] = field(default_factory=list)
    preferred_formats: List[str] = field(default_factory=list)
    available_time_daily: int = 60
    learning_style: str = "balanced"


class ContentParser(HTMLParser):
    """Simple HTML parser to extract text and metadata from web pages."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.text_content = []
        self.in_title = False
        self.in_description = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            attrs_dict = dict(attrs)
            if attrs_dict.get("name") == "description":
                self.description = attrs_dict.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title = data.strip()
        elif data.strip():
            self.text_content.append(data.strip())

    def get_text(self) -> str:
        return " ".join(self.text_content)


class ContentCrawler:
    """Web crawler to dynamically discover learning content."""

    def __init__(self, timeout: int = 10, user_agent: str = "LearnoraBot/1.0"):
        self.timeout = timeout
        self.user_agent = user_agent
        self._visited_urls = set()

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from a URL."""
        try:
            request = Request(url, headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
            })
            with urlopen(request, timeout=self.timeout) as response:
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" in content_type or "text/plain" in content_type:
                        # Read raw bytes
                        raw_data = response.read()
                        
                        # Try to decompress if gzip
                        import gzip
                        try:
                            raw_data = gzip.decompress(raw_data)
                        except:
                            pass  # Not gzipped, use as-is
                        
                        # Decode to string
                        return raw_data.decode("utf-8", errors="ignore")
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_html(self, html_content: str) -> Dict[str, Any]:
        """Parse HTML content and extract metadata."""
        parser = ContentParser()
        parser.feed(html_content)
        return {
            "title": parser.title,
            "description": parser.description,
            "text": parser.get_text()[:500],  # First 500 chars
        }

    def extract_tags(self, text: str) -> List[str]:
        """Extract potential tags from text using simple keyword matching."""
        keywords = [
            "python", "javascript", "java", "machine learning", "ai", "data science",
            "web development", "programming", "tutorial", "course", "beginner",
            "intermediate", "advanced", "api", "database", "frontend", "backend"
        ]
        tags = []
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                tags.append(keyword)
        return tags

    def crawl_url(self, url: str, content_id: Optional[str] = None) -> Optional[LearningContent]:
        """Crawl a single URL and create a LearningContent object."""
        if url in self._visited_urls:
            return None
        
        self._visited_urls.add(url)
        html = self.fetch_url(url)
        
        if not html:
            return None
        
        parsed = self.parse_html(html)
        
        if not parsed["title"]:
            return None
        
        # Generate checksum for deduplication
        checksum = hashlib.md5(parsed["text"].encode()).hexdigest()
        
        # Extract domain as source
        domain = urlparse(url).netloc
        
        # Estimate difficulty and duration (simple heuristics)
        text = parsed["text"].lower()
        difficulty = "intermediate"
        if "beginner" in text or "introduction" in text or "basics" in text:
            difficulty = "beginner"
        elif "advanced" in text or "expert" in text or "master" in text:
            difficulty = "advanced"
        
        # Estimate duration based on text length
        word_count = len(parsed["text"].split())
        duration_minutes = max(5, min(120, word_count // 50))
        
        tags = self.extract_tags(parsed["title"] + " " + parsed["description"])
        
        content_id = content_id or hashlib.md5(url.encode()).hexdigest()[:12]
        
        return LearningContent(
            id=content_id,
            title=parsed["title"],
            content_type="article",
            source=domain,
            url=url,
            description=parsed["description"] or parsed["text"][:200],
            difficulty=difficulty,
            duration_minutes=duration_minutes,
            tags=tags,
            checksum=checksum,
            created_at=datetime.utcnow(),
        )

    def crawl_urls(self, urls: List[str]) -> List[LearningContent]:
        """Crawl multiple URLs and return list of LearningContent objects."""
        contents = []
        for url in urls:
            content = self.crawl_url(url)
            if content:
                contents.append(content)
        return contents


class NaturalLanguageProcessor:
    """Process and understand natural language queries with true NLP capabilities."""
    
    def __init__(self):
        # Synonym mappings for query expansion
        self.synonyms = {
            # Programming languages
            "python": ["python", "py"],
            "javascript": ["javascript", "js", "ecmascript", "node"],
            "java": ["java"],
            "cpp": ["cpp", "c++", "cplusplus"],
            "csharp": ["c#", "csharp", "dotnet"],
            
            # Machine Learning / AI
            "ml": ["machine learning", "ml"],
            "ai": ["artificial intelligence", "ai"],
            "deep learning": ["deep learning", "dl", "neural networks"],
            "data science": ["data science", "ds", "data analysis"],
            
            # Web Development
            "web dev": ["web development", "web dev", "web programming"],
            "frontend": ["frontend", "front-end", "client-side", "ui development"],
            "backend": ["backend", "back-end", "server-side", "api development"],
            
            # General terms
            "programming": ["programming", "coding", "development", "software development"],
            "tutorial": ["tutorial", "guide", "walkthrough", "how-to", "lesson"],
            "course": ["course", "class", "training", "workshop"],
            "beginner": ["beginner", "novice", "starter", "introductory", "basic"],
            "intermediate": ["intermediate", "medium", "moderate"],
            "advanced": ["advanced", "expert", "professional", "master"],
            "learn": ["learn", "study", "master", "understand"],
        }
        
        # Intent patterns
        self.intent_patterns = {
            "learning": [
                r"\b(learn|learning|study|understand|master)\b",
                r"\b(want to|need to|how to|how do i)\b",
                r"\b(teach me|show me|help me)\b",
            ],
            "tutorial": [
                r"\b(tutorial|guide|walkthrough|how-?to)\b",
                r"\b(step by step|example|demo)\b",
            ],
            "reference": [
                r"\b(reference|documentation|docs|manual|api)\b",
                r"\b(lookup|look up|find|search)\b",
            ],
            "project": [
                r"\b(project|build|create|make|develop)\b",
                r"\b(application|app|program|software)\b",
            ],
        }
        
        # Difficulty patterns
        self.difficulty_patterns = {
            "beginner": [
                r"\b(beginner|novice|starter|new|introduction|intro|basic|fundamentals|getting started)\b",
                r"\b(never|first time|starting out|new to)\b",
            ],
            "intermediate": [
                r"\b(intermediate|medium|moderate|some experience)\b",
            ],
            "advanced": [
                r"\b(advanced|expert|professional|master|in-?depth|complex)\b",
            ],
        }
        
        # Format patterns
        self.format_patterns = {
            "video": [r"\b(video|videos|watch|visual|screencast)\b"],
            "article": [r"\b(article|articles|read|text|blog|post)\b"],
            "course": [r"\b(course|courses|class|training)\b"],
            "tutorial": [r"\b(tutorial|tutorials|guide|walkthrough)\b"],
            "book": [r"\b(book|books|ebook|e-book)\b"],
        }
        
        # Stop words to filter out
        self.stop_words = {
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
            "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
            "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
            "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
            "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
            "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
            "at", "by", "for", "with", "about", "against", "between", "into", "through",
            "during", "before", "after", "above", "below", "to", "from", "up", "down",
            "in", "out", "on", "off", "over", "under", "again", "further", "then",
            "once", "here", "there", "when", "where", "why", "how", "all", "both",
            "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
            "only", "own", "same", "so", "than", "too", "very", "can", "will", "just",
            "should", "now",
        }
    
    def expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms."""
        query_lower = query.lower()
        expanded_terms = set()
        
        # Add original query terms
        for word in query_lower.split():
            if word not in self.stop_words:
                expanded_terms.add(word)
        
        # Add synonyms
        for key, synonyms in self.synonyms.items():
            if key in query_lower or any(syn in query_lower for syn in synonyms):
                expanded_terms.update(synonyms)
        
        # Combine original query with expanded terms
        expanded = query + " " + " ".join(expanded_terms)
        return expanded
    
    def extract_intent(self, query: str) -> Dict[str, Any]:
        """Extract user intent from query."""
        query_lower = query.lower()
        intents = {}
        
        for intent_name, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += 1
            if score > 0:
                intents[intent_name] = score
        
        # Get primary intent (highest score)
        primary_intent = max(intents.items(), key=lambda x: x[1])[0] if intents else "general"
        
        return {
            "primary": primary_intent,
            "all_intents": intents,
            "confidence": max(intents.values()) / len(self.intent_patterns) if intents else 0.0
        }
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract topics, difficulty, and format from query."""
        query_lower = query.lower()
        entities = {
            "topics": [],
            "difficulty": [],
            "formats": [],
        }
        
        # Extract topics from synonyms
        for key, synonyms in self.synonyms.items():
            if any(syn in query_lower for syn in synonyms):
                if key not in ["learn", "tutorial", "course", "beginner", "intermediate", "advanced"]:
                    entities["topics"].append(key)
        
        # Extract difficulty level
        for difficulty, patterns in self.difficulty_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    entities["difficulty"].append(difficulty)
                    break
        
        # Extract preferred format
        for format_type, patterns in self.format_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    entities["formats"].append(format_type)
                    break
        
        return entities
    
    def extract_key_terms(self, query: str) -> List[str]:
        """Extract important terms from query, filtering stop words."""
        query_lower = query.lower()
        # Remove punctuation
        translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
        clean_query = query_lower.translate(translator)
        
        # Extract terms, filter stop words
        terms = [
            term for term in clean_query.split()
            if term and term not in self.stop_words and len(term) > 2
        ]
        
        return terms
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Comprehensive query processing with all NLP features."""
        return {
            "original_query": query,
            "expanded_query": self.expand_query(query),
            "intent": self.extract_intent(query),
            "entities": self.extract_entities(query),
            "key_terms": self.extract_key_terms(query),
        }


class APIContentFetcher:
    """Fetch content from educational APIs."""

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.api_keys = api_keys or {}

    def fetch_youtube_content(self, query: str, max_results: int = 10) -> List[LearningContent]:
        """Simulate fetching YouTube educational content."""
        # Note: This is a placeholder. Real implementation would use YouTube Data API
        print(f"Would fetch YouTube content for: {query}")
        return []

    def fetch_medium_content(self, query: str, max_results: int = 10) -> List[LearningContent]:
        """Simulate fetching Medium articles."""
        # Note: This is a placeholder. Real implementation would use Medium API
        print(f"Would fetch Medium content for: {query}")
        return []

    def fetch_github_content(self, query: str, max_results: int = 10) -> List[LearningContent]:
        """Simulate fetching GitHub repositories and documentation."""
        # Note: This is a placeholder. Real implementation would use GitHub API
        print(f"Would fetch GitHub content for: {query}")
        return []

    def fetch_coursera_content(self, query: str, max_results: int = 10) -> List[LearningContent]:
        """Simulate fetching Coursera courses."""
        # Note: This is a placeholder. Real implementation would use Coursera API
        print(f"Would fetch Coursera content for: {query}")
        return []


class VectorDBManager:
    """In-memory index that supports BM25, dense and hybrid search."""

    def __init__(self) -> None:
        self._contents: Dict[str, LearningContent] = {}
        self._tokenized_docs: Dict[str, List[str]] = {}
        self._tfidf_vectors: Dict[str, Dict[str, float]] = {}
        self._vector_norms: Dict[str, float] = {}
        self._doc_freq: Dict[str, int] = {}
        self._doc_lengths: Dict[str, int] = {}
        self._avg_doc_len: float = 0.0

    def add_contents(self, contents: Iterable[LearningContent]) -> None:
        """Add or replace a batch of contents and rebuild indices."""

        updated = False
        for content in contents:
            updated = True
            self._contents[content.id] = content
        if updated:
            self._rebuild_indices()

    @property
    def contents(self) -> Dict[str, LearningContent]:
        return self._contents

    def search(
        self,
        query: str,
        top_k: int = 10,
        strategy: str = "hybrid",
        *,
        dense_weight: float = 0.65,
    ) -> List[Tuple[LearningContent, float]]:
        """Return ranked results for *query* using the desired strategy.

        Args:
            query: The free form search string.
            top_k: Maximum number of results to return.
            strategy: One of ``"dense"``, ``"bm25"`` or ``"hybrid"``.
            dense_weight: Combination weight used for the hybrid mode.
        """

        if not query.strip():
            return []

        if strategy not in {"dense", "bm25", "hybrid"}:
            raise ValueError(f"Unsupported strategy '{strategy}'.")

        bm25_scores = self._bm25_scores(query)
        dense_scores = self._dense_scores(query)

        if strategy == "bm25":
            combined = bm25_scores
        elif strategy == "dense":
            combined = dense_scores
        else:
            combined = self._combine_scores(bm25_scores, dense_scores, dense_weight)

        ordered_ids = sorted(combined, key=combined.get, reverse=True)
        results: List[Tuple[LearningContent, float]] = []
        for content_id in ordered_ids[:top_k]:
            results.append((self._contents[content_id], combined[content_id]))
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        translator = str.maketrans({c: " " for c in string.punctuation})
        clean = text.translate(translator).lower()
        return [token for token in clean.split() if token]

    def _rebuild_indices(self) -> None:
        self._tokenized_docs.clear()
        self._tfidf_vectors.clear()
        self._vector_norms.clear()
        self._doc_freq.clear()
        self._doc_lengths.clear()

        for content_id, content in self._contents.items():
            tokens = self._tokenize(content.document_text())
            self._tokenized_docs[content_id] = tokens
            token_counts: Dict[str, int] = {}
            for token in tokens:
                self._doc_freq[token] = self._doc_freq.get(token, 0) + 1
                token_counts[token] = token_counts.get(token, 0) + 1
            self._doc_lengths[content_id] = len(tokens)
            self._tfidf_vectors[content_id] = token_counts

        total_docs = len(self._contents)
        if total_docs == 0:
            self._avg_doc_len = 0.0
            return

        self._avg_doc_len = sum(self._doc_lengths.values()) / total_docs

        for content_id, token_counts in self._tfidf_vectors.items():
            tfidf_vector: Dict[str, float] = {}
            norm = 0.0
            for token, count in token_counts.items():
                tf = 1 + math.log(count)
                df = self._doc_freq[token]
                idf = math.log((total_docs + 1) / (df + 1)) + 1
                value = tf * idf
                tfidf_vector[token] = value
                norm += value * value
            self._tfidf_vectors[content_id] = tfidf_vector
            self._vector_norms[content_id] = math.sqrt(norm) if norm else 0.0

    def _dense_scores(self, query: str) -> Dict[str, float]:
        tokens = self._tokenize(query)
        if not tokens:
            return {}
        query_counts: Dict[str, int] = {}
        for token in tokens:
            query_counts[token] = query_counts.get(token, 0) + 1

        total_docs = len(self._contents)
        query_vector: Dict[str, float] = {}
        norm = 0.0
        for token, count in query_counts.items():
            tf = 1 + math.log(count)
            df = self._doc_freq.get(token)
            if not df:
                continue
            idf = math.log((total_docs + 1) / (df + 1)) + 1
            value = tf * idf
            query_vector[token] = value
            norm += value * value
        query_norm = math.sqrt(norm) if norm else 0.0

        scores: Dict[str, float] = {}
        if not query_vector:
            return scores
        for content_id, doc_vector in self._tfidf_vectors.items():
            numerator = 0.0
            for token, weight in query_vector.items():
                numerator += weight * doc_vector.get(token, 0.0)
            doc_norm = self._vector_norms.get(content_id, 0.0)
            if numerator and doc_norm and query_norm:
                scores[content_id] = numerator / (doc_norm * query_norm)
        return scores

    def _bm25_scores(
        self,
        query: str,
        *,
        k1: float = 1.6,
        b: float = 0.75,
    ) -> Dict[str, float]:
        tokens = self._tokenize(query)
        scores: Dict[str, float] = {}
        if not tokens:
            return scores
        total_docs = len(self._contents)
        for token in tokens:
            df = self._doc_freq.get(token)
            if not df:
                continue
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            for content_id, doc_tokens in self._tokenized_docs.items():
                freq = doc_tokens.count(token)
                if not freq:
                    continue
                numerator = freq * (k1 + 1)
                denominator = freq + k1 * (1 - b + b * self._doc_lengths[content_id] / (self._avg_doc_len or 1))
                scores[content_id] = scores.get(content_id, 0.0) + idf * (numerator / denominator)
        return scores

    @staticmethod
    def _combine_scores(
        bm25_scores: Dict[str, float],
        dense_scores: Dict[str, float],
        dense_weight: float,
    ) -> Dict[str, float]:
        combined: Dict[str, float] = {}
        for content_id, score in bm25_scores.items():
            combined[content_id] = combined.get(content_id, 0.0) + (1 - dense_weight) * score
        for content_id, score in dense_scores.items():
            combined[content_id] = combined.get(content_id, 0.0) + dense_weight * score
        return combined

    def _bm25_search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        scores = self._bm25_scores(query)
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return ordered[:top_k]


class LearnoraContentDiscovery:
    """Thin wrapper that combines search with simple personalization, dynamic content discovery, and NLP."""

    def __init__(self,
        *,
        vector_db: Optional[VectorDBManager] = None,
        openai_api_key: Optional[str] = None,
        redis_url: Optional[str] = None,
        enable_crawler: bool = True,
        enable_api_fetcher: bool = True,
        enable_nlp: bool = True,
    ) -> None:
        self.vector_db = vector_db or VectorDBManager()
        self.openai_api_key = openai_api_key
        self.redis_url = redis_url
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Dynamic content discovery components
        self.crawler = ContentCrawler() if enable_crawler else None
        self.api_fetcher = APIContentFetcher({"openai": openai_api_key}) if enable_api_fetcher else None
        self._auto_discovery_enabled = False
        
        # Natural Language Processing
        self.nlp = NaturalLanguageProcessor() if enable_nlp else None

    def _cache_key(self, query: str, user_profile: UserProfile, strategy: str) -> str:
        profile_dict = asdict(user_profile)
        return f"{query}|{strategy}|{sorted(profile_dict.items())}"

    def enable_auto_discovery(self, enabled: bool = True) -> None:
        """Enable or disable automatic content discovery."""
        self._auto_discovery_enabled = enabled

    def crawl_and_index_urls(self, urls: List[str]) -> int:
        """Crawl URLs and add discovered content to the index."""
        if not self.crawler:
            raise RuntimeError("Crawler is not enabled")
        
        contents = self.crawler.crawl_urls(urls)
        if contents:
            self.vector_db.add_contents(contents)
        return len(contents)

    def fetch_and_index_from_apis(self, query: str, sources: Optional[List[str]] = None) -> int:
        """Fetch content from external APIs and add to index."""
        if not self.api_fetcher:
            raise RuntimeError("API fetcher is not enabled")
        
        sources = sources or ["youtube", "medium", "github"]
        all_contents = []
        
        for source in sources:
            if source == "youtube":
                all_contents.extend(self.api_fetcher.fetch_youtube_content(query))
            elif source == "medium":
                all_contents.extend(self.api_fetcher.fetch_medium_content(query))
            elif source == "github":
                all_contents.extend(self.api_fetcher.fetch_github_content(query))
            elif source == "coursera":
                all_contents.extend(self.api_fetcher.fetch_coursera_content(query))
        
        if all_contents:
            self.vector_db.add_contents(all_contents)
        return len(all_contents)

    def discover_and_personalize(
        self,
        query: str,
        user_profile: UserProfile,
        *,
        strategy: str = "hybrid",
        top_k: int = 5,
        refresh_content: bool = False,
        auto_discover: Optional[bool] = None,
        discovery_sources: Optional[List[str]] = None,
        use_nlp: bool = True,
    ) -> Dict[str, Any]:
        """
        Discover and personalize content with optional automatic content discovery and NLP.
        
        Args:
            query: Search query (natural language supported)
            user_profile: User profile for personalization
            strategy: Search strategy (bm25, dense, or hybrid)
            top_k: Number of results to return
            refresh_content: Whether to bypass cache
            auto_discover: Whether to automatically discover new content (overrides instance setting)
            discovery_sources: List of sources to discover from (e.g., ["youtube", "medium"])
            use_nlp: Whether to use NLP processing on the query
        """
        # Process query with NLP if enabled
        nlp_results = None
        processed_query = query
        
        if use_nlp and self.nlp:
            nlp_results = self.nlp.process_query(query)
            processed_query = nlp_results["expanded_query"]
            
            # Update user profile based on NLP entities
            entities = nlp_results["entities"]
            if entities["formats"] and not user_profile.preferred_formats:
                user_profile.preferred_formats = entities["formats"]
        
        # Auto-discover new content if enabled
        if auto_discover is None:
            auto_discover = self._auto_discovery_enabled
        
        if auto_discover and self.api_fetcher:
            try:
                # Use expanded query for better discovery
                new_count = self.fetch_and_index_from_apis(processed_query, discovery_sources)
                if new_count > 0:
                    refresh_content = True  # Force refresh if new content was added
            except Exception as e:
                print(f"Auto-discovery failed: {e}")
        
        if not refresh_content:
            cached = self._cache.get(self._cache_key(processed_query, user_profile, strategy))
            if cached is not None:
                # Add NLP info to cached results if available
                if nlp_results:
                    cached["nlp_analysis"] = nlp_results
                return cached

        # Search with processed query
        ranked = self.vector_db.search(processed_query, top_k=top_k, strategy=strategy)
        
        # Apply NLP-based filtering if we have entities
        if nlp_results and nlp_results["entities"]["difficulty"]:
            preferred_difficulty = nlp_results["entities"]["difficulty"][0]
            ranked = self._filter_by_difficulty(ranked, preferred_difficulty)
        
        personalized = self._personalize_results(ranked, user_profile)
        
        payload = {
            "query": query,
            "processed_query": processed_query if use_nlp else query,
            "user_id": user_profile.user_id,
            "strategy": strategy,
            "results": personalized,
            "stats": {
                "total_indexed": len(self.vector_db.contents),
                "returned": len(personalized),
            },
        }
        
        # Add NLP analysis to response
        if nlp_results:
            payload["nlp_analysis"] = {
                "intent": nlp_results["intent"],
                "entities": nlp_results["entities"],
                "key_terms": nlp_results["key_terms"],
            }
        
        self._cache[self._cache_key(processed_query, user_profile, strategy)] = payload
        return payload
    
    def _filter_by_difficulty(
        self,
        ranked_results: List[Tuple[LearningContent, float]],
        preferred_difficulty: str,
    ) -> List[Tuple[LearningContent, float]]:
        """Filter and boost results matching preferred difficulty."""
        filtered = []
        for content, score in ranked_results:
            if content.difficulty == preferred_difficulty:
                # Boost matching difficulty
                filtered.append((content, score * 1.2))
            else:
                # Keep but with lower priority
                filtered.append((content, score * 0.9))
        
        # Re-sort by adjusted scores
        filtered.sort(key=lambda x: x[1], reverse=True)
        return filtered

    def _personalize_results(
        self,
        ranked_results: Sequence[Tuple[LearningContent, float]],
        user_profile: UserProfile,
    ) -> List[Dict[str, Any]]:
        if not ranked_results:
            return []

        boost_formats = {fmt.lower() for fmt in user_profile.preferred_formats}
        available_time = user_profile.available_time_daily

        adjusted: List[Tuple[LearningContent, float]] = []
        for content, score in ranked_results:
            adjusted_score = score
            if boost_formats and content.content_type.lower() in boost_formats:
                adjusted_score *= 1.1
            if available_time and content.duration_minutes <= available_time:
                adjusted_score *= 1.05
            adjusted.append((content, adjusted_score))

        adjusted.sort(key=lambda item: item[1], reverse=True)
        result_payload: List[Dict[str, Any]] = []
        for content, score in adjusted:
            result_payload.append(
                {
                    "id": content.id,
                    "title": content.title,
                    "score": round(score, 6),
                    "url": content.url,
                    "description": content.description,
                    "content_type": content.content_type,
                    "difficulty": content.difficulty,
                    "duration_minutes": content.duration_minutes,
                    "tags": content.tags,
                }
            )
        return result_payload


def compute_ndcg(predictions: List[str], ground_truth: Dict[str, float], k: int = 10) -> float:
    """Compute the normalized discounted cumulative gain (nDCG)."""

    if not predictions or not ground_truth:
        return 0.0
    dcg = 0.0
    for rank, content_id in enumerate(predictions[:k], start=1):
        rel = ground_truth.get(content_id)
        if rel is None:
            continue
        dcg += (2 ** rel - 1) / math.log2(rank + 1)

    ideal_relevances = sorted(ground_truth.values(), reverse=True)
    ideal_dcg = 0.0
    for rank, rel in enumerate(ideal_relevances[:k], start=1):
        ideal_dcg += (2 ** rel - 1) / math.log2(rank + 1)
    return dcg / ideal_dcg if ideal_dcg else 0.0


def compute_mrr(predictions: List[str], ground_truth_set: Sequence[str]) -> float:
    """Compute the mean reciprocal rank (MRR)."""

    if not predictions or not ground_truth_set:
        return 0.0
    ground_truth = set(ground_truth_set)
    for rank, content_id in enumerate(predictions, start=1):
        if content_id in ground_truth:
            return 1.0 / rank
    return 0.0


def discover_content_from_web(urls: List[str]) -> List[LearningContent]:
    """Dynamically discover and parse content from provided URLs.
    
    This is a convenience function that creates a crawler and fetches content.
    
    Args:
        urls: List of URLs to crawl
        
    Returns:
        List of discovered LearningContent objects
    """
    crawler = ContentCrawler()
    return crawler.crawl_urls(urls)


__all__ = [
    "LearningContent",
    "UserProfile",
    "VectorDBManager",
    "LearnoraContentDiscovery",
    "ContentCrawler",
    "APIContentFetcher",
    "ContentParser",
    "NaturalLanguageProcessor",
    "compute_ndcg",
    "compute_mrr",
    "discover_content_from_web",
]