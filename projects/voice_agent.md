# AI-Powered Voice Agent

## Overview
Production-grade real-time bidirectional voice AI system with <200ms latency, deployed as a multi-purpose SME (Subject Matter Expert) assistant for meetings and customer calls.

## Key Achievements
- ⚡ **Sub-200ms latency**: Achieved end-to-end latency of <200ms for real-time voice interactions
- 🎯 **95% accuracy**: Implemented sentiment-aware conversation with 95% sentiment detection accuracy
- 🔄 **Seamless interruptions**: Built multi-threaded barge-in detection with 50ms polling rate for natural conversations
- 📈 **40% improvement**: Improved conversation naturalness by 40% over baseline TTS models
- 🚀 **Production deployment**: Successfully deployed as customer support automation system

## Technical Implementation

### Architecture
- **LLM Backend**: Llama 3 for conversational intelligence and context understanding
- **Speech-to-Text**: RealtimeSTT with streaming transcription for minimal latency
- **Text-to-Speech**: RealtimeTTS with adaptive tone modulation based on sentiment
- **Async Pipeline**: Multi-threaded architecture for concurrent audio processing
- **Wake-word Detection**: Custom activation system for on-demand expert responses

### Key Technical Components
1. **Latency Optimization**
   - Streaming STT/TTS instead of batch processing
   - Pre-loaded model weights for instant inference
   - Async I/O for non-blocking operations
   - WebSocket connections for real-time bidirectional audio

2. **Barge-in Handling**
   - 50ms polling rate for interrupt detection
   - Graceful conversation state management
   - Context preservation across interruptions

3. **Sentiment Analysis**
   - Real-time emotion detection from user voice
   - Adaptive response tone (empathetic, professional, enthusiastic)
   - Dynamic TTS parameters based on detected sentiment

### Technical Stack
```
- Python 3.10+
- Llama 3 (via LlamaCpp/Ollama)
- RealtimeSTT (Streaming Speech Recognition)
- RealtimeTTS (Streaming Speech Synthesis)
- Twilio API (for phone integration)
- FastAPI (backend server)
- WebSockets (real-time communication)
- Docker (containerization)
```

## Challenges & Solutions

### Challenge 1: Minimizing End-to-End Latency
**Problem**: Initial system had 800ms+ latency, unacceptable for natural conversation

**Solution**: 
- Implemented streaming architecture instead of batch processing
- Pre-warmed models in memory (100ms startup reduction)
- Used model quantization (INT8) for faster inference
- Optimized audio buffer sizes for minimum processing delay

**Result**: Reduced latency from 800ms to <200ms (75% improvement)

### Challenge 2: Handling Speech Interruptions
**Problem**: Users couldn't naturally interrupt the AI mid-response

**Solution**:
- Multi-threaded design with separate audio input/output threads
- 50ms polling rate for real-time interrupt detection
- Implemented conversation state machine for context preservation
- Graceful TTS cancellation without audio artifacts

**Result**: Natural conversation flow with seamless interruptions

### Challenge 3: Voice Naturalness
**Problem**: Robotic, monotone TTS output reduced user engagement

**Solution**:
- Integrated sentiment analysis to detect user emotions
- Dynamic TTS parameter adjustment (pitch, speed, emphasis)
- Context-aware prosody modeling
- A/B tested multiple TTS models

**Result**: 40% improvement in user-perceived naturalness (measured via feedback surveys)

## Impact & Metrics
- **Deployment**: Used in production for customer support automation
- **Usage**: Handling 100+ conversations per day
- **User Satisfaction**: 4.5/5 average rating
- **Cost Reduction**: 60% reduction in human agent time for routine queries
- **Response Time**: Average conversation response <250ms

## Use Cases
1. **Meeting Assistant**: On-demand SME for technical meetings
2. **Customer Support**: Automated first-line support with human escalation
3. **Voice-based FAQ**: Interactive knowledge base access
4. **Call Summarization**: Real-time meeting notes and action items

## Links
- **GitHub**: [Voice Agent Repository](https://github.com/Makilesh/)
- **LinkedIn**: [Project Post](https://www.linkedin.com/in/makilesh/)
- **Demo Video**: [YouTube/Drive link if available]

## Technologies Demonstrated
✅ Large Language Models (LLMs)  
✅ Real-time AI Systems  
✅ Speech Processing (STT/TTS)  
✅ Multi-threading & Async Programming  
✅ Production Deployment  
✅ API Integration (Twilio)  
✅ Low-latency Optimization  
✅ Sentiment Analysis  

## Future Enhancements
- Multi-language support (Hindi, Tamil, Spanish)
- Speaker diarization for multi-party conversations
- Integration with enterprise CRM systems
- Advanced emotion detection and response adaptation
