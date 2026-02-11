import os
import dspy
from dotenv import load_dotenv
from mistralai import Mistral
import time
import httpx

class MistralLM(dspy.LM):
    """
    Custom DSPy provider for Mistral AI API.
    """
    def __init__(self, model, api_key=None, **kwargs):
        super().__init__(model)
        
        # Create httpx client with SSL verification disabled for corporate proxies (Zscaler, etc.)
        # For production environments, consider using proper certificate configuration instead
        http_client = httpx.Client(verify=False)
        
        # Pass httpx.Client as 'client' parameter
        self.client = Mistral(api_key=api_key, client=http_client)
        self.kwargs = kwargs

    def basic_request(self, prompt=None, **kwargs):
        """
        Basic request method required by DSPy.
        """
        # Ensure prompt is never None
        if not prompt:
            prompt = ""
        
        # Convert prompt to OpenAI-style messages format
        messages = [{"role": "user", "content": str(prompt)}]
        
        # Map parameters to Mistral API
        temperature = kwargs.get("temperature", self.kwargs.get("temperature", 0.7))
        max_tokens = kwargs.get("max_tokens", self.kwargs.get("max_tokens", 2000))
        top_p = kwargs.get("top_p", self.kwargs.get("top_p", 1.0))
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.complete(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p
                )
                
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    if content:
                        return [content]
                return [""]
            except Exception as e:
                error_str = str(e)
                # Check for rate limit errors
                if "rate_limit" in error_str.lower() or "429" in error_str or "quota" in error_str.lower():
                    wait_time = 35 * (attempt + 1)  # Exponential backoff
                    print(f"Rate limit hit. Waiting {wait_time}s before retry {attempt+1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                print(f"Error calling Mistral: {e}")
                return [""]
        return [""]

    def __call__(self, prompt=None, **kwargs):
        """
        Call method for DSPy LM.
        Supports both:
        - String prompt: lm("text", temperature=0.7)
        - Messages format: lm(messages=[{"role": "user", "content": "text"}])
        """
        # Handle both prompt and messages formats
        if prompt is not None:
            # String prompt format
            return self.basic_request(prompt=prompt, **kwargs)
        elif "messages" in kwargs:
            # Messages format - convert to string prompt
            messages = kwargs.pop("messages")
            prompt_text = self._format_messages_to_prompt(messages)
            return self.basic_request(prompt=prompt_text, **kwargs)
        else:
            # No prompt provided
            return [""]
    
    def _format_messages_to_prompt(self, messages):
        """Convert messages format to a single prompt string."""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n".join(prompt_parts)

def configure_mistral():
    """Configures the Mistral API client using key from environment."""
    load_dotenv()
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable is not set. Please add it to a .env file.")
    
    # Configure dspy to use Mistral provider
    # Using mistral-medium-2508 as specified
    lm = MistralLM("mistral-medium-2508", api_key=api_key)
    dspy.settings.configure(lm=lm)
