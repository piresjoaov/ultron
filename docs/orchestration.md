# Orchestration and model routing

`Orchestrator` receives a terminal message, classifies it deterministically, asks `ModelRouter` for a `RoutingDecision`, then runs the OpenAI-compatible streaming client. Tool calls are validated as JSON objects and executed only from the registered tool map. At most `ULTRON_MAX_TOOL_ROUNDS` model/tool rounds run per turn.

Model text is untrusted. The CLI never renders streamed raw output: `PlainTextOutputPolicy` buffers it, removes ANSI controls and Markdown/HTML presentation syntax, then emits only canonical plain text. Metadata reports whether output was sanitized and which policy violations were observed. This boundary does not verify factual accuracy; it prevents the model from controlling terminal presentation or tool execution.

`ModelProfile` declares a stable `id`, server-facing `model_ref`, capability set, quality and speed scores, context window, tool support, enabled state, and optional endpoint. `ModelCatalog` only describes models; it selects the first enabled available profile as a safe fallback.

Classifier categories are `general`, `fast`, `coding`, `reasoning`, `long_context`, `creative`, and `vision`. The router filters disabled/incompatible models, tools and context requirements, then scores capability, quality, speed, context, and tool compatibility. If nothing qualifies it returns the configured fallback; no available profile raises an explicit error.

To add a model, add a `ModelProfile` to `ModelCatalog` (or construct the catalog with profiles) with its capabilities and endpoint. No router change is required. `AssistantResponse` already carries `visuals` as an empty list for a future frontend; rendering and visual generation are intentionally outside this phase.
