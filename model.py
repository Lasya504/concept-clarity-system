import json
import re
from urllib import error, parse, request, response
from prompt import build_prompt

model_name = "google/mt5-base"

tokenizer = None
model = None
model_error = None

REQUEST_TIMEOUT_SECONDS = 6

PREFERRED_RELATED_TERMS = {
    "dna": ["Gene", "Chromosome"],
    "rna": ["mRNA", "Protein synthesis"],
    "catalyst": ["Activation energy", "Reaction rate"],
    "catalysis": ["Activation energy", "Reaction rate"],
    "organism": ["Cell", "Species"],
    "photosynthesis": ["Chlorophyll", "Glucose"],
    "osmosis": ["Diffusion", "Semipermeable membrane"],
    "diffusion": ["Concentration gradient", "Kinetic energy"],
    "ecosystem": ["Biodiversity", "Food web"],
}

PREFERRED_EXAMPLES = {
    "dna": "Think of DNA like a gigantic blueprint or an instruction manual for a complex Lego set. Just as a manual tells you exactly where every brick goes to build a castle, DNA contains the code that tells your body how to build everything from your eyes to your heartbeat. In real life, forensic scientists use this 'manual' to solve mysteries by matching tiny biological clues to specific individuals.",
    "rna": "If DNA is the master blueprint locked in a safe, RNA is like a photocopied instruction sheet that workers take to the construction site. It carries the specific orders from the DNA to the 'protein factories' in your cell. For example, mRNA vaccines work by giving your body a temporary 'instruction sheet' to learn how to recognize and fight a specific virus.",
    "photosynthesis": "Think of photosynthesis like a solar-powered kitchen inside a leaf. Plants take 'ingredients' like sunlight, water, and carbon dioxide, and 'cook' them into glucose (sugar) which is their food. A real-world example is how sunlight hitting a cornfield eventually turns into the energy you get when you eat a corn tortilla.",
    "osmosis": "Imagine a screen door that lets air through but keeps bugs out. Osmosis is like water trying to balance itself through a similar 'screen' (a membrane). A perfect real-time example is when you put a wilted stick of celery in a glass of water; the water 'osmosis' its way into the celery cells, making it crisp and firm again.",
    "diffusion": "Diffusion is like when someone opens a bottle of perfume in the corner of a room; slowly, the scent molecules spread out until you can smell it everywhere. In your body, this happens every second when oxygen moves from your lungs (where there's a lot of it) into your blood (where there's less of it) so your muscles can keep moving.",
    "catalyst": "Think of a catalyst like a GPS for a road trip. You could find your way without it, but it would take a lot more time and energy. The GPS doesn't drive the car, but it makes the journey much faster. In real life, the catalytic converter in your car speeds up the process of turning toxic exhaust into safer gases before they leave the tailpipe.",
    "catalysis": "Think of a catalyst like a GPS for a road trip. You could find your way without it, but it would take a lot more time and energy. The GPS doesn't drive the car, but it makes the journey much faster. In real life, the catalytic converter in your car speeds up the process of turning toxic exhaust into safer gases before they leave the tailpipe.",
    "organism": "An organism is like a complete, self-running city. Whether it's a tiny single-celled bacteria or a massive blue whale, it has its own systems for power (energy), waste removal, and building new structures (growth). For example, a single mushroom in a forest is a living organism that communicates with others through underground networks to survive.",
    "ecosystem": "Think of an ecosystem like a finely tuned orchestra where every instrument—from the tiny insects (violins) to the giant trees (cellos)—must play its part to keep the music going. If you remove the wolves from a forest, the deer overpopulate and eat all the plants, 'breaking' the music. A real-world example is a coral reef, where thousands of species rely on each other to survive in the ocean.",
    "gravity": "Gravity is like an invisible elastic band that connects everything in the universe. The bigger the object, the stronger the pull. Think of how the Earth's 'elastic band' keeps your feet firmly on the ground, while also reaching out into space to keep the Moon from drifting away, creating the ocean tides we see every day.",
}

SCIENCE_GLOSSARY = {
    "dna": {
        "term": "DNA",
        "explanation": (
            "DNA (deoxyribonucleic acid) is the molecule that stores genetic instructions "
            "for growth, function, and reproduction in living organisms. It is built from "
            "four bases (A, T, C, G) arranged in a double-helix structure."
        ),
        "related_terms": ["Gene", "Chromosome"],
        "real_life_example": PREFERRED_EXAMPLES["dna"]
    },
    "rna": {
        "term": "RNA",
        "explanation": (
            "RNA (ribonucleic acid) helps convert genetic information into proteins. "
            "Unlike DNA, RNA is usually single-stranded and uses uracil (U) instead of thymine (T)."
        ),
        "related_terms": ["Protein synthesis", "mRNA"],
        "real_life_example": PREFERRED_EXAMPLES["rna"]
    },
    "photosynthesis": {
        "term": "Photosynthesis",
        "explanation": (
            "Photosynthesis is the process by which plants, algae, and some bacteria use sunlight "
            "to convert carbon dioxide and water into glucose and oxygen."
        ),
        "related_terms": ["Chlorophyll", "Glucose"],
        "real_life_example": PREFERRED_EXAMPLES["photosynthesis"]
    },
    "osmosis": {
        "term": "Osmosis",
        "explanation": (
            "Osmosis is the movement of water molecules through a semipermeable membrane "
            "from a region of lower solute concentration to higher solute concentration."
        ),
        "related_terms": ["Diffusion", "Semipermeable membrane"],
        "real_life_example": PREFERRED_EXAMPLES["osmosis"]
    },
    "diffusion": {
        "term": "Diffusion",
        "explanation": (
            "Diffusion is the net movement of particles from an area of higher concentration "
            "to an area of lower concentration due to random molecular motion."
        ),
        "related_terms": ["Concentration gradient", "Kinetic energy"],
        "real_life_example": PREFERRED_EXAMPLES["diffusion"]
    },
    "mitochondria": {
        "term": "Mitochondria",
        "explanation": (
            "Mitochondria are organelles in eukaryotic cells that produce ATP, the cell's main "
            "energy currency, through cellular respiration."
        ),
        "related_terms": ["ATP", "Cellular respiration"]
    },
    "gravity": {
        "term": "Gravity",
        "explanation": (
            "Gravity is the force of attraction between masses. Near Earth, it pulls objects "
            "toward the planet's center and gives them weight."
        ),
        "related_terms": ["Mass", "Weight"],
        "real_life_example": PREFERRED_EXAMPLES["gravity"]
    },
    "atom": {
        "term": "Atom",
        "explanation": (
            "An atom is the smallest unit of an element that retains its chemical properties. "
            "It consists of a nucleus (protons and neutrons) surrounded by electrons."
        ),
        "related_terms": ["Element", "Electron"]
    },
    "molecule": {
        "term": "Molecule",
        "explanation": (
            "A molecule is a group of two or more atoms chemically bonded together. "
            "Molecules can be made from the same element or different elements."
        ),
        "related_terms": ["Chemical bond", "Compound"]
    },
    "cell": {
        "term": "Cell",
        "explanation": (
            "A cell is the basic structural and functional unit of life. "
            "All living organisms are made of one or more cells."
        ),
        "related_terms": ["Organelle", "Tissue"]
    },
    "enzyme": {
        "term": "Enzyme",
        "explanation": (
            "An enzyme is a biological catalyst, usually a protein, that speeds up chemical reactions "
            "in living organisms without being consumed."
        ),
        "related_terms": ["Catalyst", "Active site"]
    },
    "ecosystem": {
        "term": "Ecosystem",
        "explanation": (
            "An ecosystem is a community of living organisms interacting with each other "
            "and with non-living components such as air, water, and soil."
        ),
        "related_terms": ["Biodiversity", "Food web"],
        "real_life_example": PREFERRED_EXAMPLES["ecosystem"]
    },
    "catalyst": {
        "term": "Catalyst",
        "explanation": (
            "A catalyst is a substance that increases the rate of a chemical reaction without being "
            "used up permanently in the process. It works by lowering the activation energy needed for "
            "reactants to form products, so reactions happen faster under the same conditions."
        ),
        "related_terms": ["Activation energy", "Reaction rate"],
        "real_life_example": PREFERRED_EXAMPLES["catalyst"]
    },
    "organism": {
        "term": "Organism",
        "explanation": (
            "An organism is any individual living thing, such as a bacterium, plant, fungus, or animal. "
            "Organisms carry out life processes including growth, reproduction, metabolism, and response "
            "to their environment."
        ),
        "related_terms": ["Cell", "Species"],
        "real_life_example": PREFERRED_EXAMPLES["organism"]
    },
}

STOPWORDS = {
    "about", "after", "again", "also", "among", "and", "another", "are", "because",
    "been", "being", "between", "both", "can", "cells", "concept", "each", "from",
    "have", "into", "its", "more", "most", "other", "over", "such", "that", "their",
    "them", "these", "this", "those", "through", "used", "using", "very", "when",
    "which", "with", "within", "without"
}


def _is_valid_related_term(candidate, term):
    if not candidate:
        return False

    text = candidate.strip()
    if not text:
        return False
    if ":" in text:
        return False
    if len(text) > 32:
        return False
    if re.search(r"\d", text):
        return False

    lowered = text.lower()
    lowered_term = (term or "").strip().lower()
    if lowered == lowered_term:
        return False

    banned = {"help", "template", "wikipedia", "article", "page"}
    if lowered in banned:
        return False

    return True


def _http_get_json(url):
    req = request.Request(
        url,
        headers={
            "User-Agent": "ConceptClarity/1.0 (educational app)",
            "Accept": "application/json"
        }
    )
    with request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _clean_text(text):
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned


def _first_sentences(text, max_sentences=6):
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    selected = parts[:max_sentences]
    return " ".join(selected).strip()


def _extract_related_terms(term, text):
    lowered_term = (term or "").strip().lower()
    words = re.findall(r"\b[A-Za-z][A-Za-z\-]{3,}\b", text or "")
    candidates = []
    seen = set()
    for raw in words:
        word = raw.strip()
        key = word.lower()
        if key == lowered_term or key in STOPWORDS:
            continue
        if key in seen:
            continue
        seen.add(key)
        candidates.append(word[0].upper() + word[1:])
        if len(candidates) == 2:
            break
    if len(candidates) < 2:
        return ["Scientific concept", "Real-world application"]
    return candidates


def _wikipedia_intro_links(title, term):
    try:
        parse_url = (
            "https://en.wikipedia.org/w/api.php"
            "?action=parse&prop=text&section=0&format=json"
            f"&page={parse.quote(title)}"
        )
        data = _http_get_json(parse_url)
        html = ((((data or {}).get("parse") or {}).get("text") or {}).get("*") or "")
        link_titles = re.findall(r'<a [^>]*title="([^"]+)"[^>]*>', html)

        results = []
        seen = set()
        for raw in link_titles:
            candidate = re.sub(r"\s*\(.*?\)\s*", "", raw).strip()
            key = candidate.lower()
            if not _is_valid_related_term(candidate, term):
                continue
            if key in seen:
                continue
            seen.add(key)
            results.append(candidate)
            if len(results) == 2:
                break
        if len(results) == 2:
            return results
    except (error.URLError, TimeoutError, ValueError, KeyError):
        pass
    return None


def _refine_related_terms(term, candidate_terms, explanation):
    preferred = PREFERRED_RELATED_TERMS.get((term or "").strip().lower())
    if preferred:
        return preferred

    cleaned = []
    seen = set()
    for item in (candidate_terms or []):
        candidate = re.sub(r"\s*\(.*?\)\s*", "", str(item)).strip()
        key = candidate.lower()
        if not _is_valid_related_term(candidate, term):
            continue
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(candidate)
        if len(cleaned) == 2:
            return cleaned

    fallback = _extract_related_terms(term, explanation)
    for item in fallback:
        key = item.lower()
        if key in seen:
            continue
        cleaned.append(item)
        seen.add(key)
        if len(cleaned) == 2:
            return cleaned

    while len(cleaned) < 2:
        cleaned.append("Scientific concept")
    return cleaned[:2]


def _real_life_example(term, explanation, source):
    key = (term or "").strip().lower()
    if key in PREFERRED_EXAMPLES:
        return PREFERRED_EXAMPLES[key]

    text = (explanation or "").lower()
    if any(token in text for token in ["dna", "rna", "gene", "enzyme", "organism", "cell"]):
        return f"Think of {term} as an essential gear in a clock. In the real world, biological researchers study this 'gear' to understand how the entire human body stays in sync, helping them invent new medicines that fix the clock when it breaks."
    if any(token in text for token in ["reaction", "molecule", "atom", "chemical", "catalyst"]):
        return f"Imagine {term} is like a secret ingredient in a recipe. In real-time industrial chemistry, using {term} correctly is the difference between a process that takes days and one that finishes in seconds, allowing us to create everything from batteries to clean drinking water faster and cheaper."
    if any(token in text for token in ["force", "energy", "gravity", "motion", "mass"]):
        return f"Think of {term} like the invisible rules of a sport. Just as you can't play soccer without understanding how the ball bounces, engineers can't build safe rollercoasters or skyscrapers without calculating exactly how {term} will affect every beam and bolt."
    if any(token in text for token in ["ecosystem", "species", "environment", "food web"]):
        return f"Imagine an ecosystem like a complex house of cards where {term} is one of the foundational cards. If environmental changes pull {term} out, the whole structure could wobble. Scientists study this to ensure our planet's 'house' stays standing for all living things."

    if source == "wikipedia" or source == "wiktionary":
        return f"To visualize {term}, think of it as a tool in a scientist's toolkit. Whether it's used to explain the stars or the cells in your skin, {term} provides a clear 'lens' that turns a confusing observation into a logical, understandable fact about our universe."
    return f"Think of {term} like a puzzle piece of the natural world. By understanding where this piece fits, we can see the 'big picture' of how science connects our daily lives—like the food we eat or the air we breathe—to the deep laws of nature."


def _wikipedia_related_terms(title, term, extract_text):
    intro_links = _wikipedia_intro_links(title, term)
    if intro_links:
        refined = _refine_related_terms(term, intro_links, extract_text)
        if len(refined) == 2:
            return refined

    try:
        links_url = (
            "https://en.wikipedia.org/w/api.php"
            "?action=query&prop=links&pllimit=max&format=json&redirects=1"
            f"&titles={parse.quote(title)}"
        )
        data = _http_get_json(links_url)
        pages = (((data or {}).get("query") or {}).get("pages") or {})
        page = next(iter(pages.values()), {})
        links = page.get("links") or []

        results = []
        seen = set()
        for item in links:
            name = (item or {}).get("title", "").strip()
            key = name.lower()
            if not _is_valid_related_term(name, term):
                continue
            if key in seen:
                continue
            seen.add(key)
            results.append(name)
            if len(results) == 2:
                break

        if len(results) == 2:
            return _refine_related_terms(term, results, extract_text)
    except (error.URLError, TimeoutError, ValueError, KeyError):
        pass

    return _refine_related_terms(term, [], extract_text)


def _wikipedia_explanation(term, language='en'):
    encoded = parse.quote((term or "").strip())
    if not encoded:
        return None

    try:
        # Step 1: identify a canonical article title.
        search_url = (
            f"https://{language}.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={encoded}&format=json&srlimit=1"
        )
        search_data = _http_get_json(search_url)
        hits = (((search_data or {}).get("query") or {}).get("search") or [])
        title = hits[0].get("title") if hits else term

        # Step 2: fetch fuller plain-text extract.
        extract_url = (
            f"https://{language}.wikipedia.org/w/api.php"
            "?action=query&prop=extracts&explaintext=1&redirects=1&format=json"
            f"&titles={parse.quote(title)}"
        )
        page_data = _http_get_json(extract_url)
        pages = (((page_data or {}).get("query") or {}).get("pages") or {})
        page = next(iter(pages.values()), {})
        extract = _first_sentences(page.get("extract"), max_sentences=12)
        if not extract:
            return None
        return {
            "term": title,
            "explanation": extract,
            "related_terms": _wikipedia_related_terms(title, term, extract),
            "real_life_example": _real_life_example(title, extract, "wikipedia"),
            "source": "wikipedia"
        }
    except (error.URLError, TimeoutError, ValueError, KeyError):
        return None


def _wiktionary_explanation(term, language='en'):
    encoded = parse.quote((term or "").strip())
    if not encoded:
        return None

    try:
        url = (
            f"https://{language}.wiktionary.org/w/api.php"
            "?action=query&prop=extracts&explaintext=1&exintro=1&redirects=1&format=json"
            f"&titles={encoded}"
        )
        data = _http_get_json(url)
        pages = (((data or {}).get("query") or {}).get("pages") or {})
        page = next(iter(pages.values()), {})
        extract = _first_sentences(page.get("extract"), max_sentences=8)
        if not extract:
            return None
        readable_term = page.get("title") or term
        return {
            "term": readable_term,
            "explanation": extract,
            "related_terms": _refine_related_terms(readable_term, [], extract),
            "real_life_example": _real_life_example(readable_term, extract, "wiktionary"),
            "source": "wiktionary"
        }
    except (error.URLError, TimeoutError, ValueError, KeyError):
        return None


def _load_model_once():
    global tokenizer, model, model_error

    if tokenizer is not None and model is not None:
        return True

    if model_error is not None:
        return False

    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

        # Use only local cache to avoid startup hangs in restricted/offline envs.
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, local_files_only=True)
        return True
    except Exception as exc:
        model_error = str(exc)
        return False


def _fallback_explanation(term, language='en'):
    cleaned = (term or "").strip()
    readable = cleaned if cleaned else "Unknown term"

    explanation = (
        f"{readable} is a scientific concept. It describes an idea, object, process, or living system "
        "used to explain how the natural world works. A complete explanation usually includes what it is, "
        "how it works, why it matters, and where it is observed in real life."
    )
    example = (
        f"Example: In school labs, students study {readable} by making observations, comparing outcomes, "
        "and linking results to scientific principles."
    )
    return {
        "term": readable,
        "explanation": f"{explanation} {example}",
        "related_terms": ["Observation", "Hypothesis"],
        "real_life_example": _real_life_example(readable, explanation, "fallback"),
        "source": "fallback"
    }


def _glossary_explanation(term, language='en'):
    key = (term or "").strip().lower()
    hit = SCIENCE_GLOSSARY.get(key)
    if not hit:
        return None
    enriched = dict(hit)
    if not enriched.get("real_life_example"):
        enriched["real_life_example"] = _real_life_example(enriched.get("term", term), enriched.get("explanation", ""), "glossary")
    enriched["source"] = "glossary"
    return enriched


def _extract_json_object(text):
    if not text:
        return None

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _normalize_response(term, payload):
    if not isinstance(payload, dict):
        return _fallback_explanation(term)

    normalized = {
        "term": payload.get("term") or term,
        "explanation": payload.get("explanation") or _fallback_explanation(term)["explanation"],
        "related_terms": _refine_related_terms(
            payload.get("term") or term,
            payload.get("related_terms") or [],
            payload.get("explanation") or ""
        ),
        "real_life_example": payload.get("real_life_example") or _real_life_example(
            payload.get("term") or term,
            payload.get("explanation") or "",
            payload.get("source") or "model"
        ),
        "source": payload.get("source") or "model"
    }
    return normalized

def _generate_quiz(term, explanation):

    if not explanation:
        return None

    short = explanation[:80] + "..."

    return {
        "questions":[
            {
                "question": f"What does {term} mainly describe?",
                "options":[
                    short,
                    "A programming language",
                    "A mechanical device",
                    "A computer algorithm"
                ],
                "answer": short
            },
            {
                "question": f"Which field commonly studies {term}?",
                "options":[
                    "Physics / Biology / Chemistry",
                    "Cooking",
                    "Music",
                    "Fashion"
                ],
                "answer": "Physics / Biology / Chemistry"
            },
            {
                "question": f"Why is {term} important?",
                "options":[
                    "It helps explain how the natural world works",
                    "It is used for entertainment",
                    "It replaces electricity",
                    "It creates internet signals"
                ],
                "answer": "It helps explain how the natural world works"
            }
        ]
    }
def generate_explanation(term, language='en'):

    wiki_hit = _wikipedia_explanation(term, language)
    if wiki_hit:
        wiki_hit["quiz"] = _generate_quiz(wiki_hit["term"], wiki_hit["explanation"])
        return wiki_hit

    wiktionary_hit = _wiktionary_explanation(term, language)
    if wiktionary_hit:
        wiktionary_hit["quiz"] = _generate_quiz(wiktionary_hit["term"], wiktionary_hit["explanation"])
        return wiktionary_hit

    glossary_hit = _glossary_explanation(term, language)
    if glossary_hit:
        glossary_hit["quiz"] = _generate_quiz(glossary_hit["term"], glossary_hit["explanation"])
        return glossary_hit

    prompt = build_prompt(term, language)

    if not _load_model_once():
        fallback = _fallback_explanation(term, language)
        fallback["quiz"] = _generate_quiz(fallback["term"], fallback["explanation"])
        return fallback

    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

        outputs = model.generate(
            **inputs,
            max_length=520,
            temperature=0.4,
            do_sample=True
        )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        parsed = _extract_json_object(response)

        response = _normalize_response(term, parsed)
        response["quiz"] = _generate_quiz(response["term"], response["explanation"])

        return response

    except Exception:
        fallback = _fallback_explanation(term, language)
        fallback["quiz"] = _generate_quiz(fallback["term"], fallback["explanation"])
        return fallback