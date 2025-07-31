import json
import os
import argparse
import requests
import time
from datetime import datetime
from collections import Counter, defaultdict
import re
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DiscordPsychoAnalyzer:
    def __init__(self, api_key=None, model="deepseek-chat"):
        """
        Initialize the psychological analyzer with DeepSeek API.
        
        Args:
            api_key: DeepSeek API key (will load from env if not provided)
            model: Model name to use (default: deepseek-chat)
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.model = model
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.analysis_results = {}
        
        # Token limits for iterative processing
        self.max_prompt_chars = 25000  # Conservative limit for DeepSeek
        self.max_tokens_per_request = 4000
        
        if not self.api_key:
            raise ValueError("DeepSeek API key not found. Set DEEPSEEK_API_KEY in .env file or pass as parameter.")
        
    def check_api_connection(self):
        """Check if DeepSeek API is accessible."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple request
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            response = requests.post(self.api_url, json=test_payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"Error connecting to DeepSeek API: {e}"
    
    def query_deepseek(self, prompt, max_tokens=4000):
        """Send a query to DeepSeek API and get the response."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=120
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                print(f"Error querying DeepSeek: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error in DeepSeek query: {e}")
            return None
    
    def load_user_data(self, file_path):
        """Load user data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user data: {e}")
            return None
    
    def extract_content_only(self, user_data):
        """Extract only the content fields from all messages."""
        messages = user_data.get('messages', [])
        
        # Extract only content fields, filtering out empty ones
        content_list = []
        for msg in messages:
            content = msg.get('content', '').strip()
            if content:  # Skip empty messages
                content_list.append(content)
        
        return content_list
    
    def analyze_temporal_patterns(self, user_data):
        """Analyze temporal patterns in messaging behavior."""
        messages = user_data.get('messages', [])
        
        if not messages:
            return {}
        
        timestamps = []
        message_lengths = []
        
        for msg in messages:
            if msg.get('content', '').strip():
                try:
                    # Parse timestamp
                    ts = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                    timestamps.append(ts)
                    message_lengths.append(len(msg['content']))
                except:
                    continue
        
        if not timestamps:
            return {}
        
        # Extract temporal features
        hours = [ts.hour for ts in timestamps]
        days = [ts.weekday() for ts in timestamps]  # 0=Monday
        months = [ts.month for ts in timestamps]
        
        # Activity patterns
        hour_counts = Counter(hours)
        day_counts = Counter(days)
        
        # Circadian analysis
        night_owl_score = sum(hour_counts[h] for h in list(range(22, 24)) + list(range(0, 6)))
        early_bird_score = sum(hour_counts[h] for h in range(6, 10))
        total_messages = len(timestamps)
        
        # Message frequency analysis
        dates = [ts.date() for ts in timestamps]
        date_counts = Counter(dates)
        
        # Emotional circadian patterns (longer messages might indicate different emotional states)
        hourly_avg_length = {}
        for hour in range(24):
            hour_messages = [length for ts, length in zip(timestamps, message_lengths) if ts.hour == hour]
            hourly_avg_length[hour] = sum(hour_messages) / len(hour_messages) if hour_messages else 0
        
        return {
            'most_active_hours': hour_counts.most_common(5),
            'most_active_days': day_counts.most_common(7),
            'night_owl_percentage': (night_owl_score / total_messages) * 100,
            'early_bird_percentage': (early_bird_score / total_messages) * 100,
            'activity_consistency': len(set(hours)) / 24,  # How spread out their activity is
            'weekend_vs_weekday': {
                'weekend': sum(day_counts[d] for d in [5, 6]),  # Sat, Sun
                'weekday': sum(day_counts[d] for d in range(5))
            },
            'message_frequency_variability': len(set(date_counts.values())),
            'peak_activity_hour': hour_counts.most_common(1)[0][0] if hour_counts else None,
            'hourly_message_lengths': hourly_avg_length,
            'temporal_span_days': (max(timestamps) - min(timestamps)).days if len(timestamps) > 1 else 0
        }
    
    def analyze_linguistic_patterns(self, content_list):
        """Analyze linguistic and writing patterns."""
        if not content_list:
            return {}
        
        all_text = ' '.join(content_list)
        
        # Basic linguistic metrics
        total_chars = len(all_text)
        total_words = len(all_text.split())
        sentences = len([msg for msg in content_list if msg.endswith(('.', '!', '?'))])
        
        # Advanced patterns
        question_ratio = len([msg for msg in content_list if '?' in msg]) / len(content_list)
        exclamation_ratio = len([msg for msg in content_list if '!' in msg]) / len(content_list)
        caps_ratio = len([msg for msg in content_list if msg.isupper() and len(msg) > 2]) / len(content_list)
        
        # Emotional indicators
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000027BF]')
        emoji_count = len(emoji_pattern.findall(all_text))
        
        # Profanity and intensity
        profanity_indicators = ['fuck', 'shit', 'damn', 'wtf', 'lmao', 'lmbo', 'hell']
        profanity_count = sum(all_text.lower().count(word) for word in profanity_indicators)
        
        # Repetition patterns (indicates emphasis or emotional state)
        repeated_chars = len(re.findall(r'(.)\1{2,}', all_text))  # Words with repeated chars
        
        # Abbreviation usage (indicates informality/age)
        abbreviations = ['lol', 'omg', 'btw', 'tbh', 'imo', 'smh', 'ngl', 'fr', 'rn']
        abbrev_count = sum(all_text.lower().count(abbr) for abbr in abbreviations)
        
        # Typo indicators (might indicate emotional state, haste, or other factors)
        potential_typos = len(re.findall(r'\b\w*[aeiou]{3,}\w*\b|\b\w*[bcdfghjklmnpqrstvwxyz]{3,}\w*\b', all_text.lower()))
        
        return {
            'avg_message_length': total_chars / len(content_list),
            'avg_words_per_message': total_words / len(content_list),
            'question_frequency': question_ratio,
            'exclamation_frequency': exclamation_ratio,
            'caps_usage': caps_ratio,
            'emoji_density': emoji_count / len(content_list),
            'profanity_frequency': profanity_count / len(content_list),
            'repetition_indicators': repeated_chars / len(content_list),
            'abbreviation_usage': abbrev_count / len(content_list),
            'potential_typo_rate': potential_typos / total_words if total_words > 0 else 0,
            'sentence_completion_rate': sentences / len(content_list)
        }
    
    def analyze_social_dynamics(self, user_data):
        """Analyze social interaction patterns and relationships."""
        messages = user_data.get('messages', [])
        
        if not messages:
            return {}
        
        mentioned_users = Counter()
        channel_activity = Counter()
        reaction_patterns = {'given': 0, 'received': 0}
        
        # Conversation threading (replies)
        reply_patterns = {'makes_replies': 0, 'receives_replies': 0}
        
        for msg in messages:
            # Track mentions
            mentions = msg.get('mentions', [])
            for mention in mentions:
                if isinstance(mention, dict):
                    mentioned_users[mention.get('username', mention.get('id', 'unknown'))] += 1
                else:
                    mentioned_users[str(mention)] += 1
            
            # Track channel activity
            channel = msg.get('channel_name', 'unknown')
            channel_activity[channel] += 1
            
            # Track reactions received
            reactions = msg.get('reactions', [])
            reaction_patterns['received'] += sum(r.get('count', 0) for r in reactions)
            
            # Check for reply indicators
            content = msg.get('content', '').lower()
            if any(indicator in content for indicator in ['@', 'reply', 'responding to', '^']):
                reply_patterns['makes_replies'] += 1
        
        # Social metrics
        total_messages = len([m for m in messages if m.get('content', '').strip()])
        unique_mentioned_users = len(mentioned_users)
        
        return {
            'most_mentioned_users': mentioned_users.most_common(10),
            'unique_people_mentioned': unique_mentioned_users,
            'mentions_per_message': sum(mentioned_users.values()) / total_messages if total_messages > 0 else 0,
            'channel_distribution': channel_activity.most_common(),
            'avg_reactions_received': reaction_patterns['received'] / total_messages if total_messages > 0 else 0,
            'reply_frequency': reply_patterns['makes_replies'] / total_messages if total_messages > 0 else 0,
            'social_engagement_score': (unique_mentioned_users + reply_patterns['makes_replies']) / total_messages if total_messages > 0 else 0
        }
    
    def analyze_emotional_indicators(self, content_list):
        """Analyze emotional patterns and mental health indicators."""
        if not content_list:
            return {}
        
        all_text = ' '.join(content_list).lower()
        
        # Emotional word categories
        positive_words = ['happy', 'great', 'awesome', 'love', 'amazing', 'perfect', 'wonderful', 'excited', 'joy', 'fantastic']
        negative_words = ['sad', 'hate', 'terrible', 'awful', 'depressed', 'angry', 'frustrated', 'disappointed', 'worried', 'stressed']
        anxiety_words = ['anxious', 'nervous', 'worried', 'scared', 'panic', 'stress', 'overwhelming', 'can\'t', 'fear']
        depression_words = ['depressed', 'hopeless', 'empty', 'worthless', 'tired', 'exhausted', 'numb', 'alone', 'isolat']
        
        # Self-reference patterns
        self_words = ['i am', 'i feel', 'i think', 'i believe', 'i want', 'i need', 'i have', 'myself', 'my life']
        
        # Crisis indicators
        crisis_words = ['kill myself', 'want to die', 'end it all', 'can\'t go on', 'suicide', 'hurt myself']
        
        # Support seeking
        support_words = ['help', 'advice', 'support', 'talk to someone', 'therapist', 'counselor']
        
        # Count occurrences
        emotional_metrics = {
            'positive_sentiment': sum(all_text.count(word) for word in positive_words),
            'negative_sentiment': sum(all_text.count(word) for word in negative_words),
            'anxiety_indicators': sum(all_text.count(word) for word in anxiety_words),
            'depression_indicators': sum(all_text.count(word) for word in depression_words),
            'self_reflection': sum(all_text.count(phrase) for phrase in self_words),
            'crisis_indicators': sum(all_text.count(phrase) for phrase in crisis_words),
            'support_seeking': sum(all_text.count(word) for word in support_words)
        }
        
        # Emotional volatility (rapid changes in message tone)
        message_emotions = []
        for msg in content_list:
            msg_lower = msg.lower()
            pos_score = sum(msg_lower.count(word) for word in positive_words)
            neg_score = sum(msg_lower.count(word) for word in negative_words)
            message_emotions.append(pos_score - neg_score)
        
        # Calculate emotional volatility
        emotion_changes = 0
        if len(message_emotions) > 1:
            for i in range(1, len(message_emotions)):
                if (message_emotions[i] > 0) != (message_emotions[i-1] > 0):
                    emotion_changes += 1
        
        emotional_metrics['emotional_volatility'] = emotion_changes / len(content_list) if content_list else 0
        emotional_metrics['overall_sentiment_score'] = (emotional_metrics['positive_sentiment'] - emotional_metrics['negative_sentiment']) / len(content_list)
        
        return emotional_metrics
    
    def chunk_messages(self, content_list, max_chars_per_chunk=20000):
        """Split messages into chunks that fit within API limits."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for content in content_list:
            content_with_quotes = f'"{content}"'
            content_length = len(content_with_quotes) + 1  # +1 for newline
            
            # If adding this message would exceed the limit, start a new chunk
            if current_length + content_length > max_chars_per_chunk and current_chunk:
                chunks.append(current_chunk.copy())
                current_chunk = [content]
                current_length = content_length
            else:
                current_chunk.append(content)
                current_length += content_length
        
        # Add the last chunk if it has content
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def create_initial_analysis_prompt(self, username, content_chunk, chunk_num, total_chunks, temporal_data=None, linguistic_data=None, social_data=None, emotional_data=None):
        """Create the initial analysis prompt for the first chunk with enhanced data."""
        content_text = '\n'.join([f'"{content}"' for content in content_chunk])
        
        # Build additional context sections
        context_sections = []
        
        if temporal_data:
            context_sections.append(f"""
**TEMPORAL PATTERNS:**
- Most active hours: {temporal_data.get('most_active_hours', [])}
- Peak activity: {temporal_data.get('peak_activity_hour', 'Unknown')}:00
- Night owl tendency: {temporal_data.get('night_owl_percentage', 0):.1f}%
- Early bird tendency: {temporal_data.get('early_bird_percentage', 0):.1f}%
- Activity consistency: {temporal_data.get('activity_consistency', 0):.2f} (0-1 scale)
- Active time span: {temporal_data.get('temporal_span_days', 0)} days""")
        
        if linguistic_data:
            context_sections.append(f"""
**LINGUISTIC PATTERNS:**
- Avg message length: {linguistic_data.get('avg_message_length', 0):.1f} chars
- Question frequency: {linguistic_data.get('question_frequency', 0):.3f}
- Exclamation usage: {linguistic_data.get('exclamation_frequency', 0):.3f}
- Caps usage: {linguistic_data.get('caps_usage', 0):.3f}
- Emoji density: {linguistic_data.get('emoji_density', 0):.2f} per message
- Profanity frequency: {linguistic_data.get('profanity_frequency', 0):.3f}
- Abbreviation usage: {linguistic_data.get('abbreviation_usage', 0):.3f}""")
        
        if social_data:
            context_sections.append(f"""
**SOCIAL PATTERNS:**
- Unique people mentioned: {social_data.get('unique_people_mentioned', 0)}
- Most mentioned users: {social_data.get('most_mentioned_users', [])[:5]}
- Social engagement score: {social_data.get('social_engagement_score', 0):.3f}
- Reply frequency: {social_data.get('reply_frequency', 0):.3f}
- Channel distribution: {social_data.get('channel_distribution', [])[:3]}""")
        
        if emotional_data:
            context_sections.append(f"""
**EMOTIONAL INDICATORS:**
- Overall sentiment: {emotional_data.get('overall_sentiment_score', 0):.3f}
- Positive sentiment: {emotional_data.get('positive_sentiment', 0)} occurrences
- Negative sentiment: {emotional_data.get('negative_sentiment', 0)} occurrences
- Anxiety indicators: {emotional_data.get('anxiety_indicators', 0)} occurrences
- Depression indicators: {emotional_data.get('depression_indicators', 0)} occurrences
- Emotional volatility: {emotional_data.get('emotional_volatility', 0):.3f}
- Crisis indicators: {emotional_data.get('crisis_indicators', 0)} occurrences
- Support seeking: {emotional_data.get('support_seeking', 0)} occurrences""")
        
        additional_context = "\n".join(context_sections)
        
        prompt = f"""You are analyzing Discord messages from user: {username}

This is chunk {chunk_num} of {total_chunks} total chunks of their messages.

{additional_context}

Message Contents (Chunk {chunk_num}):
{content_text}

Please provide a comprehensive psychological analysis including:

1. **Geographic Analysis**: Determine likely country/city from language patterns, cultural references, slang, timezone clues, and activity patterns.

2. **Big Five Personality Assessment** (rate 1-10 with detailed reasoning):
   - Openness to Experience
   - Conscientiousness
   - Extraversion  
   - Agreeableness
   - Neuroticism

3. **Sexuality & Relationships**: 
   - Sexual orientation assessment
   - Relationship status and patterns
   - Dating preferences and romantic interests
   - Attachment style indicators

4. **Social Dynamics**: 
   - Key relationships and social connections
   - Social hierarchy and influence patterns
   - Communication style in different contexts
   - Leadership vs. follower tendencies

5. **Mental Health Assessment**:
   - Emotional regulation patterns
   - Stress indicators and coping mechanisms
   - Depression/anxiety risk factors
   - Resilience and support systems
   - Crisis indicators (if any)

6. **Cognitive & Behavioral Profile**:
   - Intelligence indicators and learning style
   - Decision-making patterns
   - Risk tolerance and impulsivity
   - Attention and focus patterns
   - Memory and recall indicators

7. **Lifestyle & Temporal Analysis**:
   - Sleep patterns and circadian rhythms
   - Work/life balance indicators
   - Activity patterns and energy levels
   - Substance use indicators (if any)

8. **Communication Psychology**:
   - Verbal/digital communication style
   - Emotional expression patterns
   - Conflict resolution style
   - Humor and creativity indicators

9. **Values & Belief Systems**:
   - Core values and moral framework
   - Political/social beliefs
   - Spiritual/religious indicators
   - Life philosophy and worldview

10. **Risk Assessment**:
    - Mental health concerns
    - Behavioral red flags
    - Support system strength
    - Protective factors

Since this is chunk {chunk_num} of {total_chunks}, provide initial assessments but note areas needing more data.

CRITICAL: End with a concise summary of key findings to carry forward to the next iteration.
"""
        return prompt
    
    def create_refinement_prompt(self, username, content_chunk, chunk_num, total_chunks, previous_analysis):
        """Create a refinement prompt for subsequent chunks."""
        content_text = '\n'.join([f'"{content}"' for content in content_chunk])
        
        prompt = f"""You are continuing comprehensive psychological analysis of Discord user: {username}

This is chunk {chunk_num} of {total_chunks} total chunks.

PREVIOUS ANALYSIS SUMMARY:
{previous_analysis}

NEW MESSAGE CONTENT (Chunk {chunk_num}):
{content_text}

Please update and refine your psychological analysis by:

1. **Geographic Assessment**: Confirm or adjust location estimates with new evidence
2. **Big Five Personality Updates**: Revise scores (1-10) if new patterns emerge
3. **Sexuality/Relationship Analysis**: Add context or refine previous assessments
4. **Social Dynamics**: Update relationship observations and social patterns
5. **Mental Health Indicators**: Note any changes in emotional patterns or risk factors
6. **Behavioral Insights**: Add new lifestyle or cognitive patterns
7. **Topic Interests**: Update interests and focus areas
8. **New Observations**: Highlight significant new findings from this chunk

Focus on:
- How this new data confirms, contradicts, or adds nuance to previous findings
- New patterns not seen in earlier chunks
- Stronger evidence for previous assessments
- Any concerning changes in communication or emotional patterns
- Evolution of relationships or interests over time

Provide a comprehensive updated analysis incorporating both previous findings and new insights. 

CRITICAL: End with a summary of key findings to carry forward to the next iteration.
"""
        return prompt
    
    def create_final_synthesis_prompt(self, username, all_previous_analyses, total_messages, total_chunks):
        """Create a final synthesis prompt to combine all analyses."""
        
        analyses_text = "\n\n---ANALYSIS ITERATION---\n\n".join(all_previous_analyses)
        
        prompt = f"""You have completed comprehensive iterative psychological analysis of Discord user: {username}

Total messages analyzed: {total_messages:,}
Analysis completed in {total_chunks} chunks with full behavioral metrics.

ALL PREVIOUS ANALYSES:
{analyses_text}

Please provide a FINAL COMPREHENSIVE PSYCHOLOGICAL REPORT synthesizing all findings:

1. **Geographic Conclusion**: Final location assessment with confidence level (1-10)

2. **Complete Big Five Personality Profile** (1-10 with comprehensive reasoning):
   - Openness to Experience: X/10 - [detailed analysis]
   - Conscientiousness: X/10 - [detailed analysis]
   - Extraversion: X/10 - [detailed analysis]
   - Agreeableness: X/10 - [detailed analysis]
   - Neuroticism: X/10 - [detailed analysis]

3. **Sexuality & Relationship Final Assessment**:
   - Sexual orientation (with confidence level 1-10)
   - Current relationship status and patterns
   - Attachment style indicators
   - Key relationships and romantic interests identified

4. **Complete Psychological Profile**:
   - Core personality description
   - Dominant communication style
   - Emotional regulation and coping mechanisms
   - Mental health status and risk factors
   - Cognitive style and intelligence indicators
   - Core values, beliefs, and worldview

5. **Behavioral & Lifestyle Summary**:
   - Daily patterns and circadian preferences
   - Primary interests and passions
   - Social interaction style and relationship patterns
   - Work/life balance and priorities
   - Stress responses and coping strategies

6. **Temporal & Social Insights**:
   - Activity patterns and energy cycles
   - Social hierarchy and influence patterns
   - Communication evolution over time
   - Key relationships and social dynamics

7. **Mental Health & Risk Assessment**:
   - Current mental health indicators
   - Risk factors and protective factors
   - Support system strength
   - Intervention recommendations (if applicable)

8. **Five Most Fascinating Psychological Insights**:
   - Unique personality characteristics
   - Surprising behavioral patterns
   - Complex psychological dynamics
   - Notable contradictions or nuances
   - Remarkable personal qualities

9. **Clinical-Style Summary**:
   - Primary personality type/classification
   - Dominant psychological themes
   - Key strengths and vulnerabilities
   - Overall psychological health assessment

10. **Confidence & Limitations**:
    - Overall confidence in analysis (1-10)
    - Areas of high vs. low certainty
    - Limitations of digital-only analysis
    - Recommendations for further assessment

This is your definitive analysis of {total_messages:,} messages with complete behavioral metrics. Provide the most thorough psychological portrait possible while maintaining professional clinical standards.
"""
        return prompt
    
    def create_refinement_prompt(self, username, content_chunk, chunk_num, total_chunks, previous_analysis):
        """Create a refinement prompt for subsequent chunks."""
        content_text = '\n'.join([f'"{content}"' for content in content_chunk])
        
        prompt = f"""You are continuing psychological analysis of Discord user: {username}

This is chunk {chunk_num} of {total_chunks} total chunks.

PREVIOUS ANALYSIS SUMMARY:
{previous_analysis}

NEW MESSAGE CONTENT (Chunk {chunk_num}):
{content_text}

Please update and refine your psychological analysis by:

1. **Confirming or adjusting** previous geographic assessments with new evidence
2. **Updating Big Five scores** if new patterns emerge (include revised scores 1-10)
3. **Refining sexuality/relationship analysis** with additional context
4. **Adding new social connections** or strengthening existing observations
5. **Enhancing psychological profile** with new insights
6. **Updating behavioral insights** with additional patterns
7. **Adding new interesting observations** from this chunk

Focus on:
- How this new data confirms, contradicts, or adds nuance to previous findings
- New patterns or behaviors not seen in earlier chunks
- Stronger evidence for previous assessments
- Any concerning or notable changes in communication patterns

Provide a comprehensive updated analysis that incorporates both previous findings and new insights. End with a summary of key findings to carry forward.
"""
        return prompt
    
    def create_final_synthesis_prompt(self, username, all_previous_analyses, total_messages, total_chunks):
        """Create a final synthesis prompt to combine all analyses."""
        
        analyses_text = "\n\n---ANALYSIS ITERATION---\n\n".join(all_previous_analyses)
        
        prompt = f"""You have completed iterative psychological analysis of Discord user: {username}

Total messages analyzed: {total_messages:,}
Analysis completed in {total_chunks} chunks.

ALL PREVIOUS ANALYSES:
{analyses_text}

Please provide a FINAL COMPREHENSIVE PSYCHOLOGICAL REPORT that synthesizes all findings:

1. **Geographic Conclusion**: Final assessment of most likely location with confidence level

2. **Final Big Five Personality Scores** (1-10 with comprehensive reasoning):
   - Openness to Experience: X/10 - [detailed reasoning]
   - Conscientiousness: X/10 - [detailed reasoning]  
   - Extraversion: X/10 - [detailed reasoning]
   - Agreeableness: X/10 - [detailed reasoning]
   - Neuroticism: X/10 - [detailed reasoning]

3. **Sexuality & Relationship Final Assessment**:
   - Sexual orientation (with confidence level)
   - Current relationship status
   - Relationship patterns and preferences
   - People of particular interest

4. **Complete Psychological Profile**:
   - Core personality description
   - Communication style analysis
   - Emotional regulation patterns
   - Mental health assessment
   - Primary coping mechanisms
   - Core values and belief systems

5. **Behavioral Summary**:
   - Lifestyle and daily patterns
   - Primary interests and hobbies
   - Social interaction style
   - Online behavior patterns

6. **Risk Assessment**: Any mental health concerns or risk factors

7. **Five Most Fascinating Insights**: The most interesting discoveries about this person

8. **Confidence Assessment**: Rate your confidence in this analysis (1-10) and explain limitations

This is your final, definitive analysis incorporating {total_messages:,} messages. Be thorough, insightful, and provide the most complete psychological portrait possible.
"""
        return prompt
    
    def analyze_user_iteratively(self, user_file_path, output_dir=None):
        """Perform iterative psychological analysis processing all messages in chunks."""
        print(f"Starting comprehensive iterative analysis of: {user_file_path}")
        
        # Check API connection
        connected, message = self.check_api_connection()
        if not connected:
            print(f"❌ DeepSeek API connection failed: {message}")
            return None
        
        print(f"✅ Connected to DeepSeek API with model: {self.model}")
        
        # Load user data
        user_data = self.load_user_data(user_file_path)
        if not user_data:
            return None
        
        user_info = user_data.get('user_info', {})
        username = user_info.get('username', 'Unknown')
        
        # Extract content
        content_list = self.extract_content_only(user_data)
        if not content_list:
            print("No message content found for analysis")
            return None
        
        print(f"📊 Found {len(content_list):,} messages with content")
        
        # Perform comprehensive data analysis
        print("🔍 Analyzing temporal patterns...")
        temporal_data = self.analyze_temporal_patterns(user_data)
        
        print("🔍 Analyzing linguistic patterns...")
        linguistic_data = self.analyze_linguistic_patterns(content_list)
        
        print("🔍 Analyzing social dynamics...")
        social_data = self.analyze_social_dynamics(user_data)
        
        print("🔍 Analyzing emotional indicators...")
        emotional_data = self.analyze_emotional_indicators(content_list)
        
        print("🔍 Analyzing content topics...")
        topic_data = self.analyze_content_topics(content_list)
        
        print("🔍 Analyzing personality indicators...")
        personality_indicators = self.analyze_personality_indicators(content_list)
        
        # Split into chunks
        chunks = self.chunk_messages(content_list, self.max_prompt_chars)
        print(f"📦 Split into {len(chunks)} chunks for iterative processing")
        
        all_analyses = []
        current_summary = ""
        
        # Process each chunk
        for i, chunk in enumerate(chunks, 1):
            print(f"\n🔍 Processing chunk {i}/{len(chunks)} ({len(chunk)} messages)...")
            
            if i == 1:
                # First chunk - initial analysis with all supplementary data
                prompt = self.create_initial_analysis_prompt(
                    username, chunk, i, len(chunks),
                    temporal_data, linguistic_data, social_data, emotional_data
                )
            else:
                # Subsequent chunks - refinement
                prompt = self.create_refinement_prompt(username, chunk, i, len(chunks), current_summary)
            
            # Query API
            print(f"   Analyzing with DeepSeek... (chunk {i}/{len(chunks)})")
            response = self.query_deepseek(prompt, self.max_tokens_per_request)
            
            if not response:
                print(f"❌ Failed to get response for chunk {i}")
                continue
            
            all_analyses.append(f"CHUNK {i} ANALYSIS:\n{response}")
            
            # Extract summary for next iteration
            lines = response.strip().split('\n')
            summary_lines = []
            found_summary = False
            for line in reversed(lines):
                if any(keyword in line.lower() for keyword in ['summary', 'key findings', 'carry forward', 'important']):
                    found_summary = True
                if found_summary or len(summary_lines) < 10:
                    summary_lines.insert(0, line)
                if found_summary and len(summary_lines) > 20:
                    break
            
            current_summary = '\n'.join(summary_lines[-15:])
            
            print(f"   ✅ Chunk {i} analyzed successfully")
            
            # Small delay to be respectful to API
            if i < len(chunks):
                time.sleep(1)
        
        # Final synthesis
        if len(chunks) > 1:
            print(f"\n🔬 Creating final comprehensive synthesis...")
            final_prompt = self.create_final_synthesis_prompt(username, all_analyses, len(content_list), len(chunks))
            final_analysis = self.query_deepseek(final_prompt, self.max_tokens_per_request)
            
            if final_analysis:
                all_analyses.append(f"FINAL COMPREHENSIVE SYNTHESIS:\n{final_analysis}")
                print("   ✅ Final synthesis completed")
            else:
                print("   ⚠️  Final synthesis failed, using last chunk analysis")
                final_analysis = all_analyses[-1] if all_analyses else "Analysis failed"
        else:
            final_analysis = all_analyses[0] if all_analyses else "Analysis failed"
        
        # Combine results
        complete_analysis = {
            'user_info': user_info,
            'content_analyzed': {
                'total_messages_with_content': len(content_list),
                'total_content_characters': sum(len(content) for content in content_list),
                'chunks_processed': len(chunks),
                'messages_per_chunk': [len(chunk) for chunk in chunks],
                'sample_content': content_list[:10] if len(content_list) > 10 else content_list
            },
            'comprehensive_metrics': {
                'temporal_patterns': temporal_data,
                'linguistic_patterns': linguistic_data,
                'social_dynamics': social_data,
                'emotional_indicators': emotional_data,
                'content_topics': topic_data,
                'personality_indicators': personality_indicators
            },
            'iterative_analyses': all_analyses,
            'final_psychological_analysis': final_analysis,
            'analysis_metadata': {
                'model_used': self.model,
                'analysis_date': datetime.now().isoformat(),
                'api_provider': 'DeepSeek',
                'iterative_processing': True,
                'comprehensive_analysis': True,
                'chunks_processed': len(chunks),
                'total_api_calls': len(chunks) + (1 if len(chunks) > 1 else 0)
            }
        }
        
        # Save results
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            
            safe_username = "".join(c for c in username if c.isalnum() or c in "._-")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save complete analysis
            output_file = os.path.join(output_dir, f"comprehensive_analysis_{safe_username}_{timestamp}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(complete_analysis, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Complete analysis saved to: {output_file}")
            
            # Save readable summary
            summary_file = os.path.join(output_dir, f"final_analysis_{safe_username}_{timestamp}.txt")
            self.create_readable_summary(complete_analysis, summary_file)
            
            # Save detailed metrics report
            metrics_file = os.path.join(output_dir, f"metrics_report_{safe_username}_{timestamp}.txt")
            self.create_metrics_report(complete_analysis, metrics_file)
            
            # Save iteration log
            log_file = os.path.join(output_dir, f"analysis_log_{safe_username}_{timestamp}.txt")
            self.create_iteration_log(complete_analysis, log_file)
            
        return complete_analysis
    
    def create_metrics_report(self, analysis, output_file):
        """Create a detailed metrics report showing all analytical data."""
        user_info = analysis['user_info']
        metrics = analysis['comprehensive_metrics']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("COMPREHENSIVE BEHAVIORAL METRICS REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"User: {user_info.get('username', 'Unknown')}\n")
            f.write(f"Analysis Date: {analysis['analysis_metadata']['analysis_date']}\n\n")
            
            # Temporal Patterns
            if 'temporal_patterns' in metrics:
                temp = metrics['temporal_patterns']
                f.write("TEMPORAL BEHAVIOR ANALYSIS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Peak Activity Hour: {temp.get('peak_activity_hour', 'Unknown')}\n")
                f.write(f"Night Owl Score: {temp.get('night_owl_percentage', 0):.1f}%\n")
                f.write(f"Early Bird Score: {temp.get('early_bird_percentage', 0):.1f}%\n")
                f.write(f"Activity Consistency: {temp.get('activity_consistency', 0):.2f}/1.0\n")
                f.write(f"Active Time Span: {temp.get('temporal_span_days', 0)} days\n")
                
                weekend_data = temp.get('weekend_vs_weekday', {})
                if weekend_data:
                    total = weekend_data.get('weekend', 0) + weekend_data.get('weekday', 0)
                    if total > 0:
                        weekend_pct = (weekend_data.get('weekend', 0) / total) * 100
                        f.write(f"Weekend Activity: {weekend_pct:.1f}%\n")
                
                f.write(f"Most Active Hours: {temp.get('most_active_hours', [])[:3]}\n")
                f.write(f"Most Active Days: {temp.get('most_active_days', [])}\n\n")
            
            # Linguistic Patterns
            if 'linguistic_patterns' in metrics:
                ling = metrics['linguistic_patterns']
                f.write("LINGUISTIC ANALYSIS\n")
                f.write("-" * 20 + "\n")
                f.write(f"Average Message Length: {ling.get('avg_message_length', 0):.1f} chars\n")
                f.write(f"Average Words per Message: {ling.get('avg_words_per_message', 0):.1f}\n")
                f.write(f"Question Frequency: {ling.get('question_frequency', 0):.3f}\n")
                f.write(f"Exclamation Frequency: {ling.get('exclamation_frequency', 0):.3f}\n")
                f.write(f"Caps Usage Rate: {ling.get('caps_usage', 0):.3f}\n")
                f.write(f"Emoji Density: {ling.get('emoji_density', 0):.2f} per message\n")
                f.write(f"Profanity Frequency: {ling.get('profanity_frequency', 0):.3f}\n")
                f.write(f"Abbreviation Usage: {ling.get('abbreviation_usage', 0):.3f}\n")
                f.write(f"Repetition Indicators: {ling.get('repetition_indicators', 0):.3f}\n")
                f.write(f"Potential Typo Rate: {ling.get('potential_typo_rate', 0):.3f}\n\n")
            
            # Social Dynamics
            if 'social_dynamics' in metrics:
                social = metrics['social_dynamics']
                f.write("SOCIAL INTERACTION ANALYSIS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Unique People Mentioned: {social.get('unique_people_mentioned', 0)}\n")
                f.write(f"Mentions per Message: {social.get('mentions_per_message', 0):.3f}\n")
                f.write(f"Social Engagement Score: {social.get('social_engagement_score', 0):.3f}\n")
                f.write(f"Reply Frequency: {social.get('reply_frequency', 0):.3f}\n")
                f.write(f"Average Reactions Received: {social.get('avg_reactions_received', 0):.2f}\n")
                
                most_mentioned = social.get('most_mentioned_users', [])[:5]
                if most_mentioned:
                    f.write("Top Mentioned Users:\n")
                    for user, count in most_mentioned:
                        f.write(f"  - {user}: {count} mentions\n")
                
                channels = social.get('channel_distribution', [])[:3]
                if channels:
                    f.write("Most Active Channels:\n")
                    for channel, count in channels:
                        f.write(f"  - {channel}: {count} messages\n")
                f.write("\n")
            
            # Emotional Indicators
            if 'emotional_indicators' in metrics:
                emo = metrics['emotional_indicators']
                f.write("EMOTIONAL & MENTAL HEALTH ANALYSIS\n")
                f.write("-" * 40 + "\n")
                f.write(f"Overall Sentiment Score: {emo.get('overall_sentiment_score', 0):.3f}\n")
                f.write(f"Positive Sentiment Occurrences: {emo.get('positive_sentiment', 0)}\n")
                f.write(f"Negative Sentiment Occurrences: {emo.get('negative_sentiment', 0)}\n")
                f.write(f"Anxiety Indicators: {emo.get('anxiety_indicators', 0)}\n")
                f.write(f"Depression Indicators: {emo.get('depression_indicators', 0)}\n")
                f.write(f"Emotional Volatility: {emo.get('emotional_volatility', 0):.3f}\n")
                f.write(f"Self-Reflection Frequency: {emo.get('self_reflection', 0)}\n")
                f.write(f"Support Seeking Indicators: {emo.get('support_seeking', 0)}\n")
                
                crisis_count = emo.get('crisis_indicators', 0)
                if crisis_count > 0:
                    f.write(f"⚠️  CRISIS INDICATORS: {crisis_count} occurrences\n")
                f.write("\n")
            
            # Content Topics
            if 'content_topics' in metrics:
                topics = metrics['content_topics']
                f.write("CONTENT & INTEREST ANALYSIS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Technology Interest: {topics.get('technology_interest', 0):.3f}\n")
                f.write(f"Entertainment Interest: {topics.get('entertainment_interest', 0):.3f}\n")
                f.write(f"Health/Fitness Focus: {topics.get('health_fitness_interest', 0):.3f}\n")
                f.write(f"Social/Relationship Focus: {topics.get('social_relationship_focus', 0):.3f}\n")
                f.write(f"Work/Career Focus: {topics.get('work_career_focus', 0):.3f}\n\n")
            
            # Personality Indicators
            if 'personality_indicators' in metrics:
                personality = metrics['personality_indicators']
                f.write("PERSONALITY TRAIT INDICATORS\n")
                f.write("-" * 35 + "\n")
                f.write("Big Five Traits:\n")
                f.write(f"  Openness Indicators: {personality.get('openness_indicators', 0):.3f}\n")
                f.write(f"  Conscientiousness Indicators: {personality.get('conscientiousness_indicators', 0):.3f}\n")
                f.write(f"  Extraversion Indicators: {personality.get('extraversion_indicators', 0):.3f}\n")
                f.write(f"  Agreeableness Indicators: {personality.get('agreeableness_indicators', 0):.3f}\n")
                f.write(f"  Neuroticism Indicators: {personality.get('neuroticism_indicators', 0):.3f}\n")
                f.write("\nAdditional Personality Dimensions:\n")
                f.write(f"  Risk-Taking Indicators: {personality.get('risk_taking_indicators', 0):.3f}\n")
                f.write(f"  Safety-Seeking Indicators: {personality.get('safety_seeking_indicators', 0):.3f}\n")
                f.write(f"  Leadership Indicators: {personality.get('leadership_indicators', 0):.3f}\n")
                f.write(f"  Follower Indicators: {personality.get('follower_indicators', 0):.3f}\n")
                f.write(f"  Optimism Indicators: {personality.get('optimism_indicators', 0):.3f}\n")
                f.write(f"  Pessimism Indicators: {personality.get('pessimism_indicators', 0):.3f}\n")
                f.write(f"  Independence Indicators: {personality.get('independence_indicators', 0):.3f}\n")
                f.write(f"  Dependence Indicators: {personality.get('dependence_indicators', 0):.3f}\n\n")
            
            f.write("=" * 60 + "\n")
            f.write("INTERPRETATION NOTES:\n")
            f.write("- Higher scores in most metrics indicate more pronounced traits\n")
            f.write("- Emotional volatility >0.1 may indicate mood instability\n")
            f.write("- Crisis indicators >0 warrant attention and support\n")
            f.write("- Social engagement >0.3 indicates high social connectivity\n")
            f.write("- Personality indicators >0.01 suggest notable trait presence\n")
            f.write("- Risk-taking vs Safety-seeking scores show behavioral preferences\n")
            f.write("- Leadership vs Follower scores indicate social role preferences\n")
            f.write("- Optimism vs Pessimism scores reflect general outlook\n")
            f.write("- Independence vs Dependence scores show autonomy preferences\n")
            f.write("=" * 60 + "\n")
        
        print(f"📊 Detailed metrics report saved to: {output_file}")
    
    def analyze_content_topics(self, content_list):
        """Analyze topics and interests from message content."""
        if not content_list:
            return {}
        
        all_text = ' '.join(content_list).lower()
        
        # Technology topics
        tech_keywords = ['code', 'coding', 'programming', 'python', 'javascript', 'hacking', 'cybersecurity', 
                        'computer', 'software', 'tech', 'ai', 'machine learning', 'data', 'github', 'api']
        
        # Entertainment
        entertainment_keywords = ['movie', 'music', 'game', 'gaming', 'netflix', 'youtube', 'spotify', 
                                'tv show', 'anime', 'book', 'reading', 'video']
        
        # Health/fitness
        health_keywords = ['workout', 'gym', 'exercise', 'health', 'diet', 'fitness', 'running', 
                          'medication', 'doctor', 'therapy', 'mental health']
        
        # Social/relationships
        social_keywords = ['friend', 'relationship', 'dating', 'love', 'family', 'social', 'party', 
                          'hangout', 'meet', 'together']
        
        # Work/career
        work_keywords = ['work', 'job', 'career', 'business', 'money', 'salary', 'boss', 'office', 
                        'meeting', 'project', 'deadline']
        
        # Calculate topic scores
        topic_scores = {
            'technology_interest': sum(all_text.count(word) for word in tech_keywords),
            'entertainment_interest': sum(all_text.count(word) for word in entertainment_keywords),
            'health_fitness_interest': sum(all_text.count(word) for word in health_keywords),
            'social_relationship_focus': sum(all_text.count(word) for word in social_keywords),
            'work_career_focus': sum(all_text.count(word) for word in work_keywords)
        }
        
        # Normalize by message count
        message_count = len(content_list)
        for topic in topic_scores:
            topic_scores[topic] = topic_scores[topic] / message_count
        
        return topic_scores
    
    def analyze_personality_indicators(self, content_list):
        """Analyze specific personality trait indicators."""
        if not content_list:
            return {}
        
        all_text = ' '.join(content_list).lower()
        
        # Personality trait indicators
        traits = {
            'openness': ['creative', 'curious', 'imaginative', 'artistic', 'innovative', 'explore', 'learn', 'new', 
                        'experiment', 'adventure', 'abstract', 'philosophy', 'art', 'music', 'culture', 'travel',
                        'different', 'unique', 'original', 'ideas', 'think outside', 'unconventional'],
            
            'conscientiousness': ['organized', 'planned', 'schedule', 'responsible', 'careful', 'detail', 'systematic',
                                'disciplined', 'reliable', 'punctual', 'prepared', 'methodical', 'thorough', 'precise',
                                'goal', 'achieve', 'complete', 'finish', 'deadline', 'structure', 'order'],
            
            'extraversion': ['party', 'social', 'outgoing', 'energy', 'talk', 'people', 'crowd', 'fun', 'exciting',
                           'enthusiastic', 'active', 'assertive', 'dominant', 'leadership', 'center of attention',
                           'talkative', 'sociable', 'gregarious', 'lively', 'cheerful', 'optimistic'],
            
            'agreeableness': ['help', 'kind', 'caring', 'support', 'empathy', 'understanding', 'cooperation', 'nice',
                            'generous', 'considerate', 'sympathetic', 'compassionate', 'forgiving', 'trust',
                            'altruistic', 'modest', 'humble', 'polite', 'respectful', 'gentle', 'warm'],
            
            'neuroticism': ['stress', 'worry', 'anxious', 'nervous', 'emotional', 'upset', 'overwhelm', 'panic',
                          'depression', 'sad', 'angry', 'frustrated', 'irritated', 'moody', 'unstable', 'volatile',
                          'insecure', 'self-doubt', 'fear', 'tension', 'pressure', 'breakdown']
        }
        
        trait_scores = {}
        message_count = len(content_list)
        
        for trait, keywords in traits.items():
            score = sum(all_text.count(word) for word in keywords)
            trait_scores[f'{trait}_indicators'] = score / message_count if message_count > 0 else 0
        
        # Additional personality indicators
        
        # Risk-taking vs. Safety-seeking
        risk_taking = ['risk', 'gamble', 'dare', 'challenge', 'bold', 'adventure', 'try new', 'experiment']
        safety_seeking = ['safe', 'secure', 'careful', 'cautious', 'conservative', 'traditional', 'stable']
        
        trait_scores['risk_taking_indicators'] = sum(all_text.count(word) for word in risk_taking) / message_count if message_count > 0 else 0
        trait_scores['safety_seeking_indicators'] = sum(all_text.count(word) for word in safety_seeking) / message_count if message_count > 0 else 0
        
        # Leadership vs. Follower tendencies
        leadership = ['lead', 'manage', 'direct', 'command', 'control', 'decide', 'organize', 'initiative']
        follower = ['follow', 'obey', 'comply', 'submit', 'defer', 'agree with', 'go along']
        
        trait_scores['leadership_indicators'] = sum(all_text.count(word) for word in leadership) / message_count if message_count > 0 else 0
        trait_scores['follower_indicators'] = sum(all_text.count(word) for word in follower) / message_count if message_count > 0 else 0
        
        # Optimism vs. Pessimism
        optimism = ['positive', 'hopeful', 'bright', 'good', 'great', 'awesome', 'wonderful', 'amazing', 'perfect']
        pessimism = ['negative', 'hopeless', 'dark', 'bad', 'terrible', 'awful', 'horrible', 'worst', 'fail']
        
        trait_scores['optimism_indicators'] = sum(all_text.count(word) for word in optimism) / message_count if message_count > 0 else 0
        trait_scores['pessimism_indicators'] = sum(all_text.count(word) for word in pessimism) / message_count if message_count > 0 else 0
        
        # Independence vs. Dependence
        independence = ['independent', 'self-reliant', 'autonomous', 'alone', 'myself', 'own way', 'freedom']
        dependence = ['dependent', 'need help', 'rely on', 'support from', 'guidance', 'approval', 'validation']
        
        trait_scores['independence_indicators'] = sum(all_text.count(word) for word in independence) / message_count if message_count > 0 else 0
        trait_scores['dependence_indicators'] = sum(all_text.count(word) for word in dependence) / message_count if message_count > 0 else 0
        
        return trait_scores
    
    def create_readable_summary(self, analysis, output_file):
        """Create a human-readable summary focusing on the final analysis."""
        user_info = analysis['user_info']
        content_info = analysis['content_analyzed']
        final_analysis = analysis['final_psychological_analysis']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("FINAL DISCORD PSYCHOLOGICAL ANALYSIS REPORT (DeepSeek Iterative)\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"User: {user_info.get('username', 'Unknown')}\n")
            f.write(f"Display Name: {user_info.get('display_name', 'Unknown')}\n")
            f.write(f"Analysis Date: {analysis['analysis_metadata']['analysis_date']}\n")
            f.write(f"Total Messages: {content_info['total_messages_with_content']:,}\n")
            f.write(f"Content Characters: {content_info['total_content_characters']:,}\n")
            f.write(f"Chunks Processed: {content_info['chunks_processed']}\n")
            f.write(f"API Calls Made: {analysis['analysis_metadata']['total_api_calls']}\n")
            f.write(f"Model Used: {analysis['analysis_metadata']['model_used']}\n\n")
            
            f.write("-" * 80 + "\n")
            f.write("COMPREHENSIVE PSYCHOLOGICAL ANALYSIS\n")
            f.write("-" * 80 + "\n\n")
            
            f.write(final_analysis)
            
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("ANALYSIS PROCESS: This analysis used iterative processing to examine all messages\n")
            f.write("in chunks, building and refining insights with each iteration for maximum accuracy.\n\n")
            f.write("DISCLAIMER: This analysis is speculative and based on digital communication patterns.\n")
            f.write("It should not be used for clinical diagnosis or professional assessment.\n")
            f.write("This is for research and entertainment purposes only.\n")
            f.write("=" * 80 + "\n")
        
        print(f"📄 Final analysis summary saved to: {output_file}")
    
    def create_iteration_log(self, analysis, output_file):
        """Create a log showing the progression through each analysis iteration."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("ITERATIVE ANALYSIS LOG\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"User: {analysis['user_info'].get('username', 'Unknown')}\n")
            f.write(f"Total Messages: {analysis['content_analyzed']['total_messages_with_content']:,}\n")
            f.write(f"Chunks: {analysis['content_analyzed']['chunks_processed']}\n")
            f.write(f"Messages per chunk: {analysis['content_analyzed']['messages_per_chunk']}\n\n")
            
            for i, iteration in enumerate(analysis['iterative_analyses'], 1):
                f.write(f"\n{'='*50}\n")
                f.write(f"ITERATION {i}\n")
                f.write(f"{'='*50}\n\n")
                f.write(iteration)
                f.write("\n")
        
        print(f"📋 Iteration log saved to: {output_file}")
    
    # Keep the old method for backward compatibility
    def analyze_user(self, user_file_path, output_dir=None):
        """Wrapper that calls the iterative analysis method."""
        return self.analyze_user_iteratively(user_file_path, output_dir)

def find_user_files(data_directory):
    """Find all user JSON files in the data directory and subdirectories."""
    user_files = []
    
    if not os.path.exists(data_directory):
        return user_files
    
    for root, dirs, files in os.walk(data_directory):
        if os.path.basename(root) == "individual_users":
            for filename in files:
                if filename.endswith('.json'):
                    filepath = os.path.join(root, filename)
                    user_files.append(filepath)
        
        elif "individual_users" not in root:
            for filename in files:
                if filename.endswith('.json') and '_' in filename and 'complete_user_data' not in filename:
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'user_info' in data and 'messages' in data:
                                user_files.append(filepath)
                    except:
                        continue
    
    return sorted(user_files)

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Discord User Psychological Analysis Tool (DeepSeek Iterative)')
    
    parser.add_argument('--data-dir', default='output',
                      help='Directory containing Discord extraction data (default: ./output)')
    parser.add_argument('--user-id', 
                      help='Specific user ID to analyze (if not provided, will show available users)')
    parser.add_argument('--user-file',
                      help='Direct path to user JSON file')
    parser.add_argument('--output-dir', default='psychological_analysis',
                      help='Directory to save analysis results (default: psychological_analysis)')
    parser.add_argument('--model', default='deepseek-chat',
                      help='DeepSeek model to use (default: deepseek-chat)')
    parser.add_argument('--api-key',
                      help='DeepSeek API key (will use DEEPSEEK_API_KEY from .env if not provided)')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    try:
        analyzer = DiscordPsychoAnalyzer(api_key=args.api_key, model=args.model)
    except ValueError as e:
        print(f"❌ {e}")
        print("\nCreate a .env file with:")
        print("DEEPSEEK_API_KEY=your_api_key_here")
        return
    
    try:
        if args.user_file:
            if not os.path.exists(args.user_file):
                print(f"❌ User file not found: {args.user_file}")
                return
            
            print(f"Analyzing user file: {args.user_file}")
            result = analyzer.analyze_user_iteratively(args.user_file, args.output_dir)
            
        else:
            if not os.path.exists(args.data_dir):
                print(f"❌ Data directory not found: {args.data_dir}")
                return
            
            user_files = find_user_files(args.data_dir)
            if not user_files:
                print(f"❌ No user JSON files found in {args.data_dir}")
                return
            
            if args.user_id:
                target_file = None
                for file_path in user_files:
                    if args.user_id in os.path.basename(file_path):
                        target_file = file_path
                        break
                
                if not target_file:
                    print(f"❌ User ID {args.user_id} not found")
                    print("Available users:")
                    for file_path in user_files[:10]:  # Show first 10
                        basename = os.path.basename(file_path)
                        if '_' in basename:
                            username = basename.split('_')[0]
                            user_id = basename.split('_')[-1].replace('.json', '')
                            print(f"  {username} (ID: {user_id})")
                    return
                
                result = analyzer.analyze_user_iteratively(target_file, args.output_dir)
                
            else:
                # Show user selection interface
                print("Available users for comprehensive iterative analysis:")
                print("-" * 60)
                
                user_options = []
                for i, file_path in enumerate(user_files):
                    basename = os.path.basename(file_path)
                    if '_' in basename:
                        username = basename.split('_')[0]
                        user_id = basename.split('_')[-1].replace('.json', '')
                        
                        # Try to get message count for preview
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                msg_count = len([m for m in data.get('messages', []) if m.get('content', '').strip()])
                                print(f"{i+1:2d}. {username} (ID: {user_id}) - {msg_count:,} messages")
                        except:
                            print(f"{i+1:2d}. {username} (ID: {user_id}) - Unknown message count")
                        
                        user_options.append((user_id, file_path, username))
                
                if not user_options:
                    print("No valid user files found!")
                    return
                
                print(f"\nEnter number (1-{len(user_options)}) or User ID for comprehensive analysis:")
                print("Press Enter to exit")
                
                try:
                    user_input = input("> ").strip()
                    
                    if not user_input:
                        return
                    
                    if user_input.isdigit():
                        selection = int(user_input)
                        if 1 <= selection <= len(user_options):
                            selected_user_id, target_file, username = user_options[selection - 1]
                            print(f"\nSelected: {username} (ID: {selected_user_id})")
                        else:
                            print("❌ Invalid selection")
                            return
                    else:
                        target_file = None
                        for uid, fpath, uname in user_options:
                            if uid == user_input:
                                target_file = fpath
                                username = uname
                                break
                        
                        if not target_file:
                            print(f"❌ User ID '{user_input}' not found")
                            return
                    
                    result = analyzer.analyze_user_iteratively(target_file, args.output_dir)
                    
                except (KeyboardInterrupt, ValueError):
                    print("\n⏹️  Cancelled")
                    return
        
        if result:
            print(f"\n🎉 COMPREHENSIVE ITERATIVE ANALYSIS COMPLETED!")
            print(f"📊 Processed {result['content_analyzed']['total_messages_with_content']:,} messages")
            print(f"📦 Used {result['content_analyzed']['chunks_processed']} chunks")
            print(f"🔄 Made {result['analysis_metadata']['total_api_calls']} API calls")
            print(f"📈 Generated comprehensive behavioral metrics")
            print(f"📁 Results saved to: {args.output_dir}/")
            print("\n📋 Files created:")
            print("  - comprehensive_analysis_[user]_[timestamp].json (Complete data)")
            print("  - final_analysis_[user]_[timestamp].txt (Human-readable final report)")
            print("  - metrics_report_[user]_[timestamp].txt (Detailed behavioral metrics)")
            print("  - analysis_log_[user]_[timestamp].txt (Iteration progression log)")
        else:
            print("❌ Analysis failed.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
