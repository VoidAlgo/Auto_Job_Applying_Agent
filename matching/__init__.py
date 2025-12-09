"""
Matching Module - Intelligent Job Matching Engine

This module provides intelligent matching between candidate profiles and job postings
using NLP, semantic embeddings, and multi-criteria scoring.

Components:
    - SkillExtractor: Extract and normalize skills from job descriptions
    - JobMatcher: Semantic similarity matching between jobs and profiles
    - JobRanker: Multi-criteria ranking with weighted scoring

Author: Auto Job Applier System
Date: December 2025
"""

from matching.skill_extractor import SkillExtractor, ExtractedSkills
from matching.job_matcher import JobMatcher, MatchScore
from matching.ranker import JobRanker, RankedJob

__all__ = [
    'SkillExtractor',
    'ExtractedSkills',
    'JobMatcher',
    'MatchScore',
    'JobRanker',
    'RankedJob',
]
