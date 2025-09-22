from typing import Optional, Dict


class LLMClient:
    """
    Abstract LLM client. Implement generate(prompt) -> text.
    """

    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError


class NoopLLMClient(LLMClient):
    def generate(self, prompt: str, **kwargs) -> str:
        # Just return the prompt or a short canned summary — useful for offline fallback.
        return " ".join(prompt.splitlines())[:1000]  # naive fallback


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        try:
            import openai
        except Exception as e:
            raise RuntimeError("OpenAI package not installed. pip install openai") from e
        self._openai = openai
        self._openai.api_key = api_key
        self.model = model

    def generate(self, prompt: str, max_tokens:int=512, **kwargs) -> str:
        resp = self._openai.Completion.create(
            model=self.model,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.2,
            **kwargs
        )
        # There are different response shapes depending on API version; this is simplistic:
        if "choices" in resp and len(resp.choices)>0:
            return resp.choices[0].text.strip()
        return str(resp)

