from models.types import RoutingDecision

class ModelRouter:
    def __init__(self, catalog):
        self.catalog = catalog

    def route(self, task):
        candidates = [model for model in self.catalog.enabled_models() if self.catalog.is_available(model)
            and (task.category in model.capabilities or "general" in model.capabilities)
            and (not task.requires_tools or model.supports_tools)
            and model.context_window >= task.estimated_context_tokens]
        cloud_preferred = (
            task.complexity == "high"
            or task.category in {"coding", "reasoning"}
        )
        if cloud_preferred:
            cloud_candidates = [model for model in candidates if model.requires_token]
            if cloud_candidates:
                selected = max(cloud_candidates, key=lambda model: (model.quality_score, model.speed_score))
                return RoutingDecision(selected.id, task.category, "Cloud model selected for complex coding or reasoning task", task.confidence, False)
        if candidates:
            def score(model):
                return ((100 if task.category in model.capabilities else 0) + model.quality_score * 10 + model.speed_score * task.preferred_speed + 20 + (50 if task.requires_tools and model.supports_tools else 0))
            selected = max(candidates, key=score)
            return RoutingDecision(selected.id, task.category, f"{task.category} task; selected highest compatible score", task.confidence, False)
        fallback = self.catalog.fallback()
        if fallback:
            return RoutingDecision(fallback.id, task.category, "No fully compatible model available; using configured fallback", task.confidence * 0.7, True)
        raise RuntimeError("No enabled, available model exists in the catalog")
