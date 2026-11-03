# spikes

Throwaway experiments that answer one question before we build the real thing. Each folder runs on its own with `uv run` and declares its dependencies inside the script (PEP 723), so heavy packages stay out of the main lockfile.

Tests here use the standard library and mocks only, and never call a real API. Stable code moves to `ml/` or `apps/api`, and the spike gets deleted.
