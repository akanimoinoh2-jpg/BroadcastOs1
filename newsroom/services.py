import re

from django.utils.text import slugify

KEYWORDS = [
    'breaking', 'live', 'exclusive', 'headline', 'report', 'interview',
    'analysis', 'investigation', 'update', 'alert', 'top story', 'feature',
]


def _split_sentences(text):
    chunks = re.split(r'(?<=[.!?])\s+', text.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def summarize_text(text, max_sentences=3):
    if not text:
        return ''

    sentences = _split_sentences(text)
    if len(sentences) <= max_sentences:
        return ' '.join(sentences)

    summary = ' '.join(sentences[:max_sentences])
    if len(summary) < 120 and len(sentences) > max_sentences:
        summary += ' ' + sentences[max_sentences]
    return summary.strip()


def generate_ai_headlines(text, max_headlines=3):
    if not text:
        return []

    sentences = _split_sentences(text)
    title_candidates = []
    for sentence in sentences[:6]:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue
        title_candidates.append(sentence[:90].rstrip('.,!?'))

    title_candidates = title_candidates[:max_headlines]
    if not title_candidates:
        title_candidates = ['Breaking update: newsroom report prepared for broadcast.']

    headlines = []
    for candidate in title_candidates:
        prefix = 'Breaking:' if any(keyword in candidate.lower() for keyword in KEYWORDS) else 'News:'
        headline = f"{prefix} {candidate}"
        if len(headline) > 100:
            headline = headline[:97].rstrip() + '...'
        headlines.append(headline)

    return headlines[:max_headlines]


def recommend_tags(text, max_tags=6):
    if not text:
        return []

    lower = text.lower()
    words = re.findall(r"\b[a-z]{4,}\b", lower)
    frequency = {}
    for word in words:
        if word in ('because', 'which', 'where', 'there', 'their', 'would', 'could', 'should', 'about', 'their'):
            continue
        frequency[word] = frequency.get(word, 0) + 1

    sorted_keywords = sorted(frequency.items(), key=lambda item: (-item[1], item[0]))
    tags = [word for word, _ in sorted_keywords[:max_tags]]
    if not tags:
        tags = ['newsroom', 'broadcast', 'headline']
    return tags


def build_script_outline(text, max_points=5):
    sentences = _split_sentences(text)
    outline = []
    for index, sentence in enumerate(sentences[:max_points]):
        outline.append(f"Point {index + 1}: {sentence}")
    if not outline:
        outline = ['Point 1: Draft an opening statement that summarizes the story, then add context, details, and quotes.']
    return outline


def generate_interview_questions(text, max_questions=5):
    sentences = _split_sentences(text)
    questions = []
    if not text or len(sentences) == 0:
        return [
            'What led to this story?',
            'How will this affect the audience?',
            'What supporting data can you provide?',
        ]

    keywords = set()
    for sentence in sentences[:4]:
        for word in sentence.split():
            cleaned = re.sub(r'[^a-zA-Z]', '', word).lower()
            if len(cleaned) > 5:
                keywords.add(cleaned)
    keywords = list(keywords)[:max_questions]
    for index, keyword in enumerate(keywords, start=1):
        questions.append(f"What can you tell us about {keyword}?"
                          if index % 2 == 1 else f"How does {keyword} shape the story?")

    if len(questions) < max_questions:
        questions.extend([
            'What is the most important fact viewers should remember?',
            'Who are the key people involved?',
            'What is the next step after this story?',
        ])

    return questions[:max_questions]


def generate_social_post(text, max_chars=240):
    if not text:
        return 'Breaking news from our newsroom: stay tuned for the latest updates.'

    first_sentence = _split_sentences(text)[0]
    post = f"Latest update: {first_sentence}"
    if len(post) > max_chars:
        post = post[:max_chars].rstrip(' .,!?') + '...'
    return post


def create_story_slug(title):
    return slugify(title)[:50]


def generate_script_outline(text, max_points=5):
    """Backward-compatible wrapper used by models expecting
    `generate_script_outline`. Internally reuses the simpler
    `build_script_outline` style logic.
    """
    sentences = _split_sentences(text)
    outline = []
    for index, sentence in enumerate(sentences[:max_points]):
        outline.append(f"Point {index + 1}: {sentence}")
    if not outline:
        outline = [
            'Point 1: Draft an opening statement that summarizes the story, then add context, details, and quotes.'
        ]
    return outline
