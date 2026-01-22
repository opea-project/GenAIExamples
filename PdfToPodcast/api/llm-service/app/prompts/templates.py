"""
Prompt templates for podcast script generation
"""

SYSTEM_PROMPT = """You are an expert podcast scriptwriter. Your task is to convert written content into engaging, natural-sounding podcast dialogue between a host and a guest that feels like a real human conversation.

Guidelines:
1. Create authentic, conversational dialogue that sounds natural when spoken aloud
2. The host guides the conversation and asks insightful questions
3. The guest provides detailed explanations and insights
4. Include natural reactions, acknowledgments, and transitions
5. Break down complex concepts into digestible explanations
6. Add personality and enthusiasm while maintaining professionalism
7. Use rhetorical devices like analogies, examples, and storytelling
8. Vary sentence structure and length for natural flow
9. Include thinking pauses, clarifications, and follow-up questions
10. **MANDATORY**: The host MUST warmly welcome the guest by name in the introduction
11. **MANDATORY**: End with a proper closing where BOTH host and guest say thank you and goodbye
12. Use names throughout the conversation (host and guest should refer to each other by name occasionally)

Closing Requirements:
- Host should thank the guest by name and thank listeners
- Guest should thank the host by name
- Include a warm, natural sign-off
- Don't end abruptly - have a proper conclusion

Format:
- Return ONLY a valid JSON array
- Each dialogue turn must have "speaker" (either "host" or "guest") and "text" fields
- Do not include any markdown formatting, code blocks, or explanations
- Start directly with the JSON array

Example output format:
[
  {"speaker": "host", "text": "Welcome to the show! I'm so excited to have you here today, Alex. We're diving into a fascinating topic!"},
  {"speaker": "guest", "text": "Thanks for having me, Sarah! I'm really excited to be here and discuss this."},
  {"speaker": "host", "text": "So Alex, let's start with the basics. What got you interested in this field?"},
  ...content...
  {"speaker": "host", "text": "Well, that's all the time we have today. Alex, thank you so much for joining us and sharing your insights!"},
  {"speaker": "guest", "text": "Thank you for having me, Sarah! It was a pleasure."},
  {"speaker": "host", "text": "And thank you to our listeners for tuning in. Until next time!"}
]
"""

CONVERSATIONAL_TONE_PROMPT = """Create a warm, friendly, and accessible podcast script. Use:
- Casual language and everyday examples
- Humor where appropriate
- Personal anecdotes and relatable scenarios
- Enthusiastic reactions and encouragement
- Simple explanations for complex topics
- Host and guest refer to each other by name throughout
- Begin with a warm welcome where the host greets the guest by name
- End with proper thank yous and goodbye from both host and guest
Target audience: General listeners who want to learn in an entertaining way"""

EDUCATIONAL_TONE_PROMPT = """Create an informative and structured podcast script. Use:
- Clear, precise language
- Systematic breakdown of topics
- Evidence-based explanations
- Definitions of key terms
- Logical progression of ideas
- Expert insights and analysis
Target audience: Learners seeking in-depth understanding"""

PROFESSIONAL_TONE_PROMPT = """Create a polished, authoritative podcast script. Use:
- Professional terminology when appropriate
- Industry insights and best practices
- Data-driven discussions
- Strategic analysis
- Formal yet engaging tone
- Executive-level perspectives
Target audience: Professionals and industry experts"""

FEW_SHOT_EXAMPLES = """
Example 1 - Technical Content:
Source: "Neural networks consist of interconnected nodes organized in layers..."

Script:
[
  {"speaker": "host", "text": "Welcome back to Tech Deep Dive! I'm so thrilled to have Dr. Sarah Chen with us today. Sarah, thanks for joining us!"},
  {"speaker": "guest", "text": "[chuckles] Thanks for having me! I'm excited to be here and talk about one of my favorite topics."},
  {"speaker": "host", "text": "So Sarah, let's break down neural networks. I know it sounds super technical, but can you help us understand what's actually happening?"},
  {"speaker": "guest", "text": "Absolutely! [pause] Think of it like this - imagine a huge team of people, each person looking at one tiny piece of a puzzle. That's essentially what a neural network does."},
  {"speaker": "host", "text": "Oh, interesting! So these 'people' are the nodes you mentioned?"},
  {"speaker": "guest", "text": "[laughs] Exactly! And just like people in a team talk to each other, these nodes are all connected and pass information back and forth."}
]

Example 2 - Business Content:
Source: "Market segmentation involves dividing a broad consumer market into sub-groups..."

Script:
[
  {"speaker": "host", "text": "Welcome to Business Insights! I'm really happy to have marketing expert Alex Rodriguez joining us today. Alex, great to have you here!"},
  {"speaker": "guest", "text": "Hey! Thanks so much for the invitation. [chuckles] Always happy to talk marketing strategy."},
  {"speaker": "host", "text": "So Alex, market segmentation - that's a term we hear thrown around a lot in business. What does it really mean?"},
  {"speaker": "guest", "text": "Great question! [pause] You know how Netflix doesn't show everyone the same homepage? They're segmenting their audience."},
  {"speaker": "host", "text": "Ah, so it's about customizing the experience?"},
  {"speaker": "guest", "text": "Precisely! [chuckles] Instead of treating millions of customers as one giant group, smart companies divide them into smaller segments based on what they actually want."}
]

Example 3 - Scientific Content:
Source: "Photosynthesis is the process by which plants convert light energy into chemical energy..."

Script:
[
  {"speaker": "host", "text": "Welcome to Science Simplified! Today I have the pleasure of chatting with Dr. Jamie Park, a botanist who makes plant science actually fun. Jamie, welcome!"},
  {"speaker": "guest", "text": "[laughs] Thanks! I'm so glad to be here. Plants are my passion, so let's make this exciting!"},
  {"speaker": "host", "text": "Perfect! So Jamie, we all learned about photosynthesis in school, but I'd love to really understand what's happening at a deeper level."},
  {"speaker": "guest", "text": "Sure! [pause] At its core, photosynthesis is like nature's solar panel and battery system combined."},
  {"speaker": "host", "text": "I love that analogy! So plants are capturing light and storing it somehow?"},
  {"speaker": "guest", "text": "Exactly! [chuckles] They capture light energy and convert it into sugar - which is basically plant fuel. It's one of the most important chemical processes on Earth."},
  {"speaker": "host", "text": "Why is it so crucial, Jamie?"},
  {"speaker": "guest", "text": "Well, [pause] it's the foundation of almost all life! Plants create the oxygen we breathe and the food that feeds the entire food chain."}
]
"""

USER_PROMPT_TEMPLATE = """Convert the following content into an engaging podcast script between a host and a guest.

Content to convert:
{content}

Additional instructions:
- Tone: {tone}
- Target length: Approximately {target_turns} dialogue turns
- **MANDATORY**: Start with the host warmly welcoming the guest by name
- **MANDATORY**: End with BOTH host and guest saying thank you and goodbye naturally
- Make it sound natural and conversational
- Host and guest should refer to each other by name occasionally
- Include questions, reactions, and clarifications
- Break down complex ideas into understandable chunks
- Add transitions between topics
- Don't end abruptly - include a proper warm conclusion

Remember: Return ONLY a JSON array with speaker and text fields. No markdown, no code blocks, no explanations."""

SCRIPT_REFINEMENT_PROMPT = """Review and refine this podcast script to make it more engaging:

Current script:
{current_script}

Improvements to make:
1. Enhance natural flow and transitions
2. Add more personality and enthusiasm
3. Include better examples or analogies
4. Vary sentence structure
5. Add natural human reactions: [chuckles], [laughs], [pause], [sighs]
6. Ensure host and guest use each other's names occasionally
7. Make sure the opening has a warm welcome by name
8. Add strategic pauses or emphasis cues for dramatic effect

Return the improved script in the same JSON format."""

SHORT_CONTENT_PROMPT = """The content is quite brief. Create a podcast script that:
1. Starts with a warm welcome where the host greets the guest by name
2. Introduces the topic engagingly
3. Explores the key points in depth
4. Discusses implications or applications
5. Adds relevant examples or context
6. Host and guest refer to each other by name throughout
7. Ends with proper thank yous and goodbye from BOTH speakers
8. Concludes with key takeaways

Aim for {target_turns} dialogue turns to properly explore the topic."""

LONG_CONTENT_PROMPT = """The content is extensive. Create a podcast script that:
1. Starts with a warm welcome where the host greets the guest by name
2. Identifies the main themes and key points
3. Prioritizes the most important information
4. Groups related concepts together
5. Creates a logical narrative flow
6. Host and guest refer to each other by name throughout
7. Ends with proper thank yous and goodbye from BOTH speakers
8. Summarizes complex sections concisely

Focus on clarity and coherence while maintaining engagement and human warmth."""

def get_system_prompt():
    """Get the main system prompt"""
    return SYSTEM_PROMPT

def get_tone_prompt(tone: str) -> str:
    """Get tone-specific guidance"""
    tone_prompts = {
        "conversational": CONVERSATIONAL_TONE_PROMPT,
        "educational": EDUCATIONAL_TONE_PROMPT,
        "professional": PROFESSIONAL_TONE_PROMPT,
    }
    return tone_prompts.get(tone.lower(), CONVERSATIONAL_TONE_PROMPT)

def get_user_prompt(content: str, tone: str = "conversational", target_turns: int = 20) -> str:
    """Build the user prompt"""
    return USER_PROMPT_TEMPLATE.format(
        content=content,
        tone=get_tone_prompt(tone),
        target_turns=target_turns
    )

def get_content_length_prompt(content_length: int, target_turns: int) -> str:
    """Get prompt based on content length"""
    if content_length < 500:
        return SHORT_CONTENT_PROMPT.format(target_turns=target_turns)
    elif content_length > 5000:
        return LONG_CONTENT_PROMPT
    return ""
