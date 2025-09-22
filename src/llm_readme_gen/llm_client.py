import requests


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


class DeepSeekClient(LLMClient):
    """
    Client for OpenRouter R1 API (free DeepSeek model)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://openrouter.ai/api/v1",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.chat_endpoint = f"{self.base_url}/chat/completions"

    def generate(self, prompt: str, max_tokens: int = 512, **kwargs) -> str:
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            **kwargs,
        }

        resp = requests.post(self.chat_endpoint, headers=headers, json=data)
        try:
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(
                f"OpenRouter DeepSeek API error: {resp.status_code} {resp.text}"
            ) from e

        resp_json = resp.json()
        if "choices" in resp_json and len(resp_json["choices"]) > 0:
            first = resp_json["choices"][0]
            if "message" in first and "content" in first["message"]:
                return first["message"]["content"].strip()
            elif "text" in first:
                return first["text"].strip()
        raise RuntimeError(f"Unexpected response format from OpenRouter: {resp_json}")
    