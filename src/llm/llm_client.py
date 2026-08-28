import json
import ollama


class LLMClient:
    """Local LLM client using Ollama."""

    def __init__(self, model="llama3.2:3b"):
        self.model = model
        self.enabled = self._check_model()

    def _check_model(self):
        """Check whether the Ollama model is available."""

        try:
            response = ollama.list()

            for model in response.models:
                if model.model == self.model:
                    return True

            return False

        except Exception as exc:
            print(f"Ollama connection error: {exc}")
            return False

    def generate_json(self, system_prompt, user_prompt):
        """Generate structured JSON using the local Ollama model."""

        if not self.enabled:
            return None

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                format="json",
            )

            content = response.message.content.strip()

            if not content:
                return None

            return json.loads(content)

        except Exception as exc:
            print(f"LLM unavailable: {exc}")
            return None

    def generate_stream(self, system_prompt, user_prompt):
        """
        Stream generated text from Ollama.

        Yields small text chunks as they are produced.
        """

        if not self.enabled:
            return

        try:
            stream = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                stream=True,
            )

            for chunk in stream:
                content = chunk.message.content

                if content:
                    yield content

        except Exception as exc:
            print(f"LLM streaming unavailable: {exc}")