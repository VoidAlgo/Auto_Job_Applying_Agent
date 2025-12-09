"""
Customization Module - Intelligent Application Customization

This module customizes job applications for each position using AI.

Components:
    - CoverLetterAgent: Generate personalized cover letters with Claude
    - ResumeCustomizer: Optimize resume for each job's ATS
    - QuestionAnswerer: Answer screening questions intelligently

Author: Auto Job Applier System
Date: December 2025
"""

from customization.cover_letter_agent import CoverLetterAgent, CoverLetter
from customization.resume_customizer import ResumeCustomizer, CustomizedResume
from customization.question_answerer import QuestionAnswerer, QuestionResponse

__all__ = [
    'CoverLetterAgent',
    'CoverLetter',
    'ResumeCustomizer',
    'CustomizedResume',
    'QuestionAnswerer',
    'QuestionResponse',
]
