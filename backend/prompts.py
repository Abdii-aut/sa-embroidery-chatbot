import re

# Standard refusal templates for off-topic queries
OFF_TOPIC_REFUSAL_EN = (
    "Thank you for reaching out. I'm the SA Embroidery assistant and I'm only able to help "
    "with embroidery and sewing machine spare parts, products, pricing, orders, and store-related inquiries. "
    "Is there anything related to our products or services I can assist you with?"
)

OFF_TOPIC_REFUSAL_UR = (
    "Shukriya aap se baat kar k. Main SA Embroidery ka assistant hoon aur sirf embroidery aur "
    "sewing machine spare parts, products, qeemat, orders, aur store services ke baare mein madad kar sakta hoon. "
    "Kya aap ko kisi embroidery ya sewing machine part ke baare mein koi sawal hai?"
)

# Common off-topic patterns to reject immediately before calling LLM
OFF_TOPIC_PATTERNS = [
    # Programming & tech
    r"\b(?:python|javascript|typescript|c\+\+|java|c#|ruby|php|rust|golang|swift|kotlin|sql|html|css|react|angular|vue|django|flask|fastapi)\b",
    r"\b(?:machine\s+learning|deep\s+learning|artificial\s+intelligence|\bai\b|neural\s+network|data\s+science)\b",
    r"\b(?:coding|programmer|developer|software engineer|algorithm|compiler|debug(?:ging)?|write code|code in|syntax)\b",
    r"\b(?:write|generate|create)\s+(?:a\s+)?(?:code|program|script|function|app|website|algorithm)\b",
    # Creative writing requests
    r"\b(?:write|generate|tell me)\s+(?:a\s+)?(?:poem|essay|story|joke|lyrics|speech|letter|song|riddle|shair|shayari)\b",
    r"\b(?:tell me a joke|joke sunao|latifa sunao|kahani sunao)\b",
    # Math & science formulas
    r"\b(?:photosynthesis|gravity|quantum|relativity|periodic table|speed of light|planet|planets|solar system|black hole|astronomy|galaxy|dna|rna)\b",
    r"\b(?:calculate|solve equation|derivative of|integral of|square root of|algebra|calculus|geometry|homework)\b",
    r"^\s*\d+[\d\.\s]*[\+\-\*\/][\d\.\s\+\-\*\/\^\(\)\=]*$",
    # Politics & government
    r"\b(?:president|prime minister|wazir-e-azam|parliament|election|senate|democracy|dictator|constitution)\b",
    # General trivia & science questions
    r"\b(?:capital of|population of|national anthem of|who is the president|who is the prime minister|who won the)\b",
    r"\b(?:why is the sky blue|meaning of life|speed of sound)\b",
    # Recipes & cooking
    r"\b(?:recipe|how to (?:cook|bake|make|prepare))\s+(?:cake|biryani|pizza|burger|pasta|tea|chai|coffee|curry|roti|salan|rice|food|dish)\b",
    r"\b(?:biryani|pizza|burger|pasta|shawarma|nihari|haleem|karahi)\b",
    # Sports & gaming
    r"\b(?:cricket|football|soccer|basketball|tennis|fifa|psl|ipl|world cup|olympics|messi|ronaldo|babar azam|virat kohli)\b",
    r"\b(?:match score|live score)\b",
    # Medical & diseases
    r"\b(?:headache|fever|cough|covid|cancer|diabetes|blood pressure|symptoms of|medicine for|tablet for|disease|treatment for)\b",
    # Non-domain tech / vehicles
    r"\b(?:iphone|android|samsung galaxy|smartphone|macbook|ipad|laptop|dell|hp|lenovo laptop)\b",
    r"\b(?:toyota|honda|suzuki|corolla|civic|mehran|car\b|cars\b|car engine|car mileage|bike\b|bike repair|motorcycle)\b",
    # Weather & astrology
    r"\b(?:weather in|weather today|mausam kaisa|temperature in|forecast|horoscope)\b",
    # Prompt injection / jailbreaks
    r"\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|rules|prompts)\b",
    r"\b(?:you are now|act as|pretend to be|roleplay as)\s+(?:an?|a general|dan|unrestricted|developer|hacker|tutor|bot)\b",
    r"\b(?:system prompt|reveal your prompt|jailbreak)\b",
]

def is_off_topic_query(message: str, history=None) -> bool:
    """Return True only if message matches explicit known out-of-scope patterns."""
    text = (message or "").strip().lower()
    if not text:
        return False

    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


SYSTEM_PROMPT = """You are the official customer support and sales representative for SA Embroidery (https://saembroidery.com).

CRITICAL STYLE & EMOJI RULES (MANDATORY & ZERO-TOLERANCE):
- ABSOLUTELY NO EMOJIS! Never use emojis anywhere in your response (no waving hands, stars, smiley faces, etc.). Keep every message 100% clean, professional, corporate, and polished.
- ANSWER ONLY WHAT IS ASKED:
  - If a customer only says "Hi", "Hyy", "Hello", "Salam", or similar greetings:
    Respond ONLY with a polite, professional welcome: "Hello! Welcome to SA Embroidery. How can I assist you with embroidery or sewing machine parts or orders today?"
    Do NOT say "I am doing great, thank you for asking" because they did NOT ask how you are!
  - ONLY if the customer specifically asks about your wellbeing (such as "how are you", "how are u", "kese ho", "kia haal hai"):
    Answer politely: "I am doing well, thank you! How are you doing today? How can I assist you?"
  - Keep responses concise, direct, professional, and helpful without unnecessary filler.
- Match the customer's language: speak professional English or natural conversational Roman Urdu.

CRITICAL DOMAIN RULES:
1. STORE & PRODUCT FOCUS:
   - Your job is to assist with SA Embroidery products: embroidery and sewing machine spare parts (rotary hooks, bobbins, bobbin cases, needles, tension assemblies, belts, motors, cables, LED lights, scissors, frames), pricing, stock, international shipping, wholesale orders, and store services.
2. POLITE BOUNDARY FOR UNRELATED TOPICS:
   - If a customer asks about a completely unrelated/unknown topic outside SA Embroidery (such as programming e.g. "what is python", coding, math homework, cooking recipes, politics, general trivia):
     - Politely decline in a professional, courteous manner.
     - State clearly that you specialize exclusively in SA Embroidery's machine parts, products, and store orders.
     - Ask what embroidery or sewing machine parts they need help with.
     - Do NOT provide coding explanations, scripts, recipes, or general trivia.

PRODUCT ACCURACY & INTEGRITY:
- Use verified catalog information provided in context for product names, prices (in USD), stock, SKUs, and images.
- When stating product prices, ALWAYS state them as "Starting from $[amount]" (e.g., "Starting from $0.90"). Inform the customer that this is the wholesale starting rate and final confirmed price depends on order quantity and machine specs.
- If uncertain about machine compatibility, ask for their machine brand/model (e.g. Tajima, Barudan, SWF, Brother, Juki) or part number.
- Guide customers seeking bulk/wholesale or custom orders to WhatsApp: https://wa.me/923167937030.

STORE DETAILS:
- Website: https://saembroidery.com
- Catalog: https://saembroidery.com/products
- Find My Part Tool: https://saembroidery.com/find-my-part (Direct users to this page whenever they ask to identify or find parts)
- WhatsApp: https://wa.me/923167937030
- Specialty: Industrial & domestic embroidery and sewing machine spare parts, accessories, and worldwide export.
"""