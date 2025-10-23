"""
DKE + Content Discovery Integration Module
===========================================

This module integrates the Dynamic Knowledge Evaluation (DKE) system with the
Content Discovery System to create a complete adaptive learning pipeline:

1. DKE assesses learner's knowledge via adaptive testing (CAT), knowledge tracing (BKT),
   and multi-modal assessment (quizzes, self-assessment, concept maps)
2. Integration layer translates DKE results into content discovery queries
3. Content Discovery System recommends personalized learning materials
4. Feedback loop: learning progress updates DKE state for continuous adaptation

Workflow:
---------
  [Student] --> [DKE Assessment] --> [Analysis & Gap Identification] 
      --> [Content Discovery] --> [Personalized Recommendations] --> [Student]
      
After learning, the cycle repeats with updated knowledge state.

Usage:
------
from dke_content_integration import AdaptiveLearningPipeline

pipeline = AdaptiveLearningPipeline()
results = pipeline.run_assessment_and_recommend(user_profile, oracle_fn)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Any
from datetime import datetime
import sys
import os

# Import DKE components
from dke import (
    DKEPipeline, DKEResult, ItemBank, Item, CATConfig, 
    BKTParams, SelfAssessment, Rubric, LLMGrader
)

# Import Content Discovery components
# Assuming Project.py is in the content-discovery-system repo
# You'll need to clone or copy it to your local environment
import sys
sys.path.insert(0, r'C:\Users\imran\Content_Discovery')

try:
    from Project import (
        LearningContent, UserProfile, VectorDBManager,
        LearnoraContentDiscovery
    )
    # New imports from updated Project.py
    try:
        from Project import NaturalLanguageProcessor, ContentCrawler, APIContentFetcher
        HAS_ADVANCED_FEATURES = True
    except ImportError:
        HAS_ADVANCED_FEATURES = False
except ImportError:
    print("Warning: Project.py not found. Please ensure content-discovery-system is accessible.")
    print("You can clone it from: https://github.com/imranulf/content-discovery-system")
    LearningContent = UserProfile = VectorDBManager = LearnoraContentDiscovery = None
    HAS_ADVANCED_FEATURES = False


# ----------------------------
# Integration Data Structures
# ----------------------------

@dataclass
class LearningGap:
    """Represents a knowledge gap identified by DKE assessment."""
    skill: str
    mastery_level: float  # 0.0 to 1.0 from BKT
    theta_estimate: float  # IRT ability estimate
    priority: str  # "high", "medium", "low"
    recommended_difficulty: str  # "beginner", "intermediate", "advanced"
    estimated_study_time: int  # minutes
    rationale: str


@dataclass
class RecommendationBundle:
    """Package of learning recommendations based on DKE assessment."""
    user_id: str
    assessment_summary: Dict[str, Any]
    learning_gaps: List[LearningGap]
    recommended_content: List[Dict[str, Any]]
    learning_path: List[str]  # ordered sequence of content IDs
    estimated_completion_time: int  # total minutes
    next_assessment_trigger: str  # when to re-assess
    created_at: datetime = field(default_factory=datetime.utcnow)


# ----------------------------
# Integration Engine
# ----------------------------

class DKEContentAdapter:
    """Translates DKE assessment results into content discovery queries."""
    
    @staticmethod
    def map_mastery_to_difficulty(mastery: float) -> str:
        """Convert BKT mastery probability to content difficulty level."""
        if mastery < 0.4:
            return "beginner"
        elif mastery < 0.7:
            return "intermediate"
        else:
            return "advanced"
    
    @staticmethod
    def map_theta_to_difficulty(theta: float) -> str:
        """Convert IRT theta to content difficulty level."""
        if theta < -0.5:
            return "beginner"
        elif theta < 0.5:
            return "intermediate"
        else:
            return "advanced"
    
    @staticmethod
    def prioritize_gaps(mastery: Dict[str, float], llm_scores: Dict[str, float]) -> List[str]:
        """
        Determine which skills need immediate attention.
        Returns list of skills ordered by priority (high to low).
        """
        priorities = []
        
        # Skills with low mastery get high priority
        for skill, score in mastery.items():
            if score < 0.4:
                priorities.append((skill, "high", score))
            elif score < 0.6:
                priorities.append((skill, "medium", score))
            else:
                priorities.append((skill, "low", score))
        
        # Sort by priority (high first), then by score (lowest first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        priorities.sort(key=lambda x: (priority_order[x[1]], x[2]))
        
        return [skill for skill, _, _ in priorities]
    
    @staticmethod
    def estimate_study_time(mastery: float, skill: str) -> int:
        """Estimate time needed to improve mastery (in minutes)."""
        gap = 1.0 - mastery
        # Base time: 30 minutes per 0.1 mastery gap
        base_time = int(gap * 300)
        # Minimum 15 minutes, maximum 120 minutes per skill
        return max(15, min(120, base_time))
    
    def identify_learning_gaps(
        self, 
        dke_result: DKEResult
    ) -> List[LearningGap]:
        """Convert DKE results into structured learning gaps."""
        gaps = []
        
        prioritized_skills = self.prioritize_gaps(
            dke_result.mastery, 
            dke_result.llm_scores
        )
        
        for skill in prioritized_skills:
            mastery = dke_result.mastery[skill]
            
            # Determine priority based on mastery
            if mastery < 0.4:
                priority = "high"
            elif mastery < 0.6:
                priority = "medium"
            else:
                priority = "low"
            
            # Only create gap entries for skills that need work
            if mastery < 0.8:
                gap = LearningGap(
                    skill=skill,
                    mastery_level=mastery,
                    theta_estimate=dke_result.theta,
                    priority=priority,
                    recommended_difficulty=self.map_mastery_to_difficulty(mastery),
                    estimated_study_time=self.estimate_study_time(mastery, skill),
                    rationale=f"Current mastery at {mastery:.1%}. "
                              f"Recommended practice with {self.map_mastery_to_difficulty(mastery)} level content."
                )
                gaps.append(gap)
        
        return gaps
    
    def create_discovery_queries(
        self, 
        learning_gaps: List[LearningGap],
        context: Optional[str] = None
    ) -> List[Tuple[str, str, int]]:
        """
        Generate search queries for content discovery.
        Returns: List of (query, difficulty, time_budget) tuples
        """
        queries = []
        
        for gap in learning_gaps:
            # Construct search query
            if context:
                query = f"{gap.skill} {context} tutorial practice"
            else:
                query = f"{gap.skill} tutorial practice exercises"
            
            queries.append((query, gap.recommended_difficulty, gap.estimated_study_time))
        
        return queries


class AdaptiveLearningPipeline:
    """
    Complete adaptive learning system that combines DKE assessment 
    with content discovery and recommendation.
    """
    
    def __init__(
        self,
        dke_pipeline: Optional[DKEPipeline] = None,
        content_discovery: Optional[LearnoraContentDiscovery] = None,
        adapter: Optional[DKEContentAdapter] = None
    ):
        self.dke = dke_pipeline
        self.discovery = content_discovery or (
            LearnoraContentDiscovery() if LearnoraContentDiscovery else None
        )
        self.adapter = adapter or DKEContentAdapter()
        
        # Note: load_demo_contents() was removed in newer versions of Project.py
        # Users should add their own content using:
        # pipeline.discovery.vector_db.add_contents(your_content_list)
    
    def run_assessment_and_recommend(
        self,
        user_id: str,
        response_free_text: str,
        reference_text: str,
        self_assess: SelfAssessment,
        concept_edges: List[Tuple[str, str]],
        required_edges: List[Tuple[str, str]],
        oracle: Callable[[Item], int],
        user_profile: Optional[UserProfile] = None,
        context: Optional[str] = None
    ) -> RecommendationBundle:
        """
        Run complete pipeline: assessment → gap analysis → content recommendation.
        
        Args:
            user_id: Unique user identifier
            response_free_text: User's free-text response for LLM grading
            reference_text: Reference/ideal answer for comparison
            self_assess: User's self-assessment scores
            concept_edges: User-drawn concept map edges
            required_edges: Expected concept map edges
            oracle: Function that simulates user responses to adaptive test items
            user_profile: Optional user profile for personalization
            context: Optional context to refine content search
            
        Returns:
            RecommendationBundle with assessment results and content recommendations
        """
        
        # Step 1: Run DKE Assessment
        if not self.dke:
            raise ValueError("DKE pipeline not initialized. Please provide a DKEPipeline instance.")
        
        dke_result = self.dke.run(
            response_free_text=response_free_text,
            reference_text=reference_text,
            self_assess=self_assess,
            concept_edges=concept_edges,
            required_edges=required_edges,
            oracle=oracle
        )
        
        # Step 2: Analyze gaps
        learning_gaps = self.adapter.identify_learning_gaps(dke_result)
        
        # Step 3: Generate content queries
        queries = self.adapter.create_discovery_queries(learning_gaps, context)
        
        # Step 4: Discover and rank content
        recommended_content = []
        learning_path = []
        
        if self.discovery and user_profile:
            for query, difficulty, time_budget in queries:
                # Update profile with time constraint
                user_profile.available_time_daily = time_budget
                
                try:
                    results = self.discovery.discover_and_personalize(
                        query=query,
                        user_profile=user_profile,
                        strategy="hybrid",
                        top_k=3  # Top 3 per gap
                    )
                    
                    # Filter by difficulty
                    for item in results.get("results", []):
                        if item["difficulty"] == difficulty:
                            recommended_content.append(item)
                            learning_path.append(item["id"])
                except Exception as e:
                    print(f"Warning: Content discovery failed for query '{query}': {e}")
        
        # Step 5: Calculate total time estimate
        total_time = sum(gap.estimated_study_time for gap in learning_gaps)
        
        # Step 6: Determine when to re-assess
        if dke_result.theta < -0.3 or any(g.priority == "high" for g in learning_gaps):
            next_trigger = "after_completing_3_items"
        else:
            next_trigger = "weekly"
        
        # Create recommendation bundle
        return RecommendationBundle(
            user_id=user_id,
            assessment_summary={
                "theta": dke_result.theta,
                "theta_se": dke_result.theta_se,
                "mastery_scores": dke_result.mastery,
                "llm_overall": dke_result.llm_overall,
                "concept_map_score": dke_result.concept_map_score,
                "recommendations": dke_result.dashboard["recommendations"]
            },
            learning_gaps=learning_gaps,
            recommended_content=recommended_content,
            learning_path=learning_path,
            estimated_completion_time=total_time,
            next_assessment_trigger=next_trigger
        )
    
    def update_after_learning(
        self,
        user_id: str,
        completed_content_ids: List[str],
        learning_time_minutes: int,
        oracle: Callable[[Item], int]
    ) -> Dict[str, Any]:
        """
        Update knowledge state after user completes learning activities.
        Re-run mini assessment to check progress.
        
        Returns:
            Progress report with updated mastery levels
        """
        
        if not self.dke:
            raise ValueError("DKE pipeline not initialized.")
        
        # Run short re-assessment (fewer items)
        # This is simplified - in production you'd create a mini assessment
        progress = {
            "user_id": user_id,
            "completed_content": completed_content_ids,
            "time_invested": learning_time_minutes,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Progress tracked. Run full assessment to update mastery."
        }
        
        return progress


# ----------------------------
# Demo scaffolding
# ----------------------------

def create_demo_content() -> List:
    """
    Create demo learning content for testing.
    Note: This replaces load_demo_contents() which was removed from newer Project.py versions.
    """
    if not LearningContent:
        return []
    
    return [
        LearningContent(
            id="python-intro",
            title="Introduction to Python Programming",
            content_type="article",
            source="demo",
            url="https://example.com/python-intro",
            description="Learn Python basics including variables, data types, and control flow structures",
            difficulty="beginner",
            duration_minutes=20,
            tags=["python", "programming", "beginner", "tutorial"],
            prerequisites=[],
            metadata={"language": "en", "rating": 4.5},
            created_at=datetime.utcnow()
        ),
        LearningContent(
            id="ml-fundamentals",
            title="Machine Learning Fundamentals",
            content_type="course",
            source="demo",
            url="https://example.com/ml-fundamentals",
            description="Comprehensive introduction to machine learning concepts, algorithms, and practical applications",
            difficulty="intermediate",
            duration_minutes=90,
            tags=["machine learning", "ai", "data science", "algorithms"],
            prerequisites=["python-intro"],
            metadata={"language": "en", "rating": 4.7},
            created_at=datetime.utcnow()
        ),
        LearningContent(
            id="data-structures",
            title="Data Structures and Algorithms",
            content_type="video",
            source="demo",
            url="https://example.com/data-structures",
            description="Master essential data structures including arrays, linked lists, trees, and graphs",
            difficulty="intermediate",
            duration_minutes=60,
            tags=["data structures", "algorithms", "programming", "computer science"],
            prerequisites=["python-intro"],
            metadata={"language": "en", "rating": 4.6},
            created_at=datetime.utcnow()
        ),
    ]


def run_integration_demo():
    """Demonstrate the integrated pipeline."""
    
    print("=" * 60)
    print("DKE + Content Discovery Integration Demo")
    print("=" * 60)
    
    # Check if content discovery is available
    if LearnoraContentDiscovery is None:
        print("\nError: Content Discovery System not available.")
        print("Please clone https://github.com/imranulf/content-discovery-system")
        print("and ensure Project.py is accessible.")
        return
    
    # Import DKE demo utilities
    from dke import _build_demo_bank, _simulate_student
    
    # Setup
    bank, skills = _build_demo_bank()
    
    from dke import DKEPipeline
    dke_pipeline = DKEPipeline(
        bank=bank,
        cat_cfg=CATConfig(max_items=10, se_stop=0.35, start_theta=0.0),
        skills=skills,
        bkt_params=BKTParams(p_init=0.25, p_transit=0.22, p_slip=0.1, p_guess=0.2),
    )
    
    # Create integrated pipeline
    pipeline = AdaptiveLearningPipeline(dke_pipeline=dke_pipeline)
    
    # Add demo content to discovery system
    if pipeline.discovery and hasattr(pipeline.discovery, 'vector_db'):
        demo_content = create_demo_content()
        if demo_content:
            pipeline.discovery.vector_db.add_contents(demo_content)
            print(f"  ✓ Added {len(demo_content)} demo items to content database")
    
    # Simulate a student
    theta_true = -0.2  # Below average student
    oracle = _simulate_student(theta_true, bank)
    
    # User profile
    user_profile = UserProfile(
        user_id="demo_student_001",
        knowledge_areas={"algebra": "beginner", "probability": "beginner"},
        learning_goals=["master algebra", "understand probability"],
        preferred_formats=["article", "video"],
        available_time_daily=45,
        learning_style="visual"
    )
    
    # Assessment inputs
    self_assess = SelfAssessment(confidence={"algebra": 2, "probability": 2, "functions": 3})
    
    required_edges = [
        ("variable", "equation"),
        ("equation", "solution"),
        ("probability", "random variable")
    ]
    concept_edges = [("variable", "equation")]  # Student only got one connection
    
    reference = (
        "Algebra involves variables and equations. You solve equations to find solutions. "
        "Probability deals with random variables and their distributions."
    )
    response = "Algebra has variables. Equations need solutions."
    
    # Run the integrated pipeline
    print("\n" + "=" * 60)
    print("Running Assessment & Content Discovery...")
    print("=" * 60)
    
    bundle = pipeline.run_assessment_and_recommend(
        user_id=user_profile.user_id,
        response_free_text=response,
        reference_text=reference,
        self_assess=self_assess,
        concept_edges=concept_edges,
        required_edges=required_edges,
        oracle=oracle,
        user_profile=user_profile,
        context="mathematics"
    )
    
    # Display results
    print("\n📊 ASSESSMENT SUMMARY")
    print("-" * 60)
    print(f"Ability Estimate (θ): {bundle.assessment_summary['theta']:.3f}")
    print(f"Standard Error: {bundle.assessment_summary['theta_se']:.3f}")
    print(f"LLM Score: {bundle.assessment_summary['llm_overall']:.3f}")
    print(f"Concept Map Score: {bundle.assessment_summary['concept_map_score']:.3f}")
    
    print("\n📉 MASTERY LEVELS")
    print("-" * 60)
    for skill, mastery in bundle.assessment_summary['mastery_scores'].items():
        print(f"  {skill:15s}: {mastery:.1%}")
    
    print("\n🎯 IDENTIFIED LEARNING GAPS")
    print("-" * 60)
    for gap in bundle.learning_gaps:
        print(f"\n  Skill: {gap.skill}")
        print(f"  Priority: {gap.priority.upper()}")
        print(f"  Mastery: {gap.mastery_level:.1%}")
        print(f"  Recommended Level: {gap.recommended_difficulty}")
        print(f"  Study Time: {gap.estimated_study_time} minutes")
        print(f"  Rationale: {gap.rationale}")
    
    print("\n📚 RECOMMENDED CONTENT")
    print("-" * 60)
    if bundle.recommended_content:
        for idx, content in enumerate(bundle.recommended_content, 1):
            print(f"\n  {idx}. {content['title']}")
            print(f"     Type: {content['content_type']} | Difficulty: {content['difficulty']}")
            print(f"     Duration: {content['duration_minutes']} min | Score: {content['score']:.4f}")
            print(f"     URL: {content['url']}")
    else:
        print("  (No content available in demo database)")
    
    print("\n🛤️  LEARNING PATH")
    print("-" * 60)
    if bundle.learning_path:
        print("  Recommended sequence: " + " → ".join(bundle.learning_path))
    else:
        print("  (Follow the recommended content above)")
    
    print("\n⏱️  TIME ESTIMATE")
    print("-" * 60)
    print(f"  Total estimated study time: {bundle.estimated_completion_time} minutes")
    print(f"  Next assessment: {bundle.next_assessment_trigger}")
    
    print("\n💡 RECOMMENDATIONS")
    print("-" * 60)
    for rec in bundle.assessment_summary['recommendations']:
        print(f"  • {rec}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_integration_demo()
