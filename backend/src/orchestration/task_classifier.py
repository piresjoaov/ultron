import re
from models.types import TaskProfile

CODING_TERMS = {"python", "java", "javascript", "typescript", "programação", "programming", "código", "code", "bug", "erro", "function", "class", "api", "refactor", "debug", "repository", "github", "arquivo", "file"}
REASONING_TERMS = {"compare", "analyze", "analyse", "why", "prove", "architecture", "tradeoff", "plan", "reason", "análise", "explique profundamente", "estratégia"}
TOOL_TERMS = {"encontre", "buscar", "procure", "pesquise", "search", "find", "read", "leia", "listar", "list", "arquivos", "files", "horas", "time"}

class TaskClassifier:
    def classify(self, prompt, context_messages=None):
        text = prompt.lower()
        words = set(re.findall(r"[\w-]+", text))
        prompt_tokens = max(1, len(prompt) // 4)
        context_tokens = prompt_tokens + sum(len(str(message.get("content", ""))) // 4 for message in (context_messages or []))
        coding = bool(words & CODING_TERMS) or "```" in prompt
        reasoning = bool(words & REASONING_TERMS)
        visual = any(term in text for term in ("imagem", "image", "visualização", "visualization", "diagrama", "diagram"))
        fast = any(term in text for term in ("rápido", "rapido", "quick", "fast", "breve", "brief"))
        long_context = context_tokens > 6000 or any(term in text for term in ("documento longo", "long document", "todo o contexto", "entire context"))
        requires_tools = bool(words & TOOL_TERMS) or "http" in text
        if visual: category = "vision"
        elif long_context: category = "long_context"
        elif coding: category = "coding"
        elif reasoning: category = "reasoning"
        elif fast or bool(words & {"horas", "time"}): category = "fast"
        elif any(term in text for term in ("crie", "criar", "write a story", "poema", "story")): category = "creative"
        else: category = "general"
        high = reasoning or coding or long_context or len(words) > 100
        return TaskProfile(category, requires_tools, long_context, "high" if high else "low", 5 if fast else 2, 5 if high else 3, 0.9 if category != "general" else 0.65, context_tokens)
