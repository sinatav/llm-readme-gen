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
    Client for DeepSeek API (free or paid). Compatible interface.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com",
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")  # no trailing slash
        self.chat_endpoint = f"{self.base_url}/v1/chat/completions"

    def generate(self, prompt: str, max_tokens: int = 512, **kwargs) -> str:
        """
        Uses DeepSeek to generate a description or assistant content.
        prompt is treated as user message (or multi-message). For more control, you could allow system or role prompts.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Build messages list: system + user
        # You could allow kwargs["system_prompt"] etc.
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
            raise RuntimeError(f"DeepSeek API error: {resp.status_code} {resp.text}") from e

        resp_json = resp.json()
        # The structure should be similar to OpenAI: choices -> message -> content
        # e.g. resp_json["choices"][0]["message"]["content"]
        if "choices" in resp_json and len(resp_json["choices"]) > 0:
            # Some versions may use "text" instead of "message"
            first = resp_json["choices"][0]
            if "message" in first and "content" in first["message"]:
                return first["message"]["content"].strip()
            elif "text" in first:
                return first["text"].strip()
        # fallback
        raise RuntimeError(f"Unexpected response format from DeepSeek: {resp_json}")
