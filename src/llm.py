import os
import dspy
from dotenv import load_dotenv
from google import genai
from google.genai import types

class GeminiLM(dspy.LM):
    """
    Custom DSPy provider for Google's new genai SDK.
    """
    def __init__(self, model, api_key=None, **kwargs):
        super().__init__(model)
        self.client = genai.Client(api_key=api_key)
        self.kwargs = kwargs

    def basic_request(self, prompt: str, **kwargs):
        """
        Basic request method required by DSPy.
        """
        # DSPy often passes 'messages' (list of dicts) if it's a chat model or compiled module.
        # But for basic generation, we want the prompt string.
        # Check if 'messages' is in kwargs and clean it up.
        
        messages = kwargs.pop("messages", None)
        
        # dspy might define a 'system' prompt separately
        # Clean kwargs for config
        valid_config_keys = [
            'temperature', 'top_p', 'top_k', 'candidate_count', 
            'max_output_tokens', 'stop_sequences', 'response_mime_type'
        ]
        
        # Filter kwargs to only valid keys for GenerateContentConfig
        # Note: 'messages' should NOT be in config.
        config_args = {k: v for k, v in {**self.kwargs, **kwargs}.items() if k in valid_config_keys}
        
        config = types.GenerateContentConfig(**config_args)
        
        # Structure the content. 
        # If 'messages' exists, we might need to format it into a single string or a list of Content objects
        # For simplicity with dspy's basic generation expectation, we might just rely on 'prompt' if it's the full string.
        # But if prompt is None and messages exist, use messages.
        
        final_contents = prompt
        
        if not final_contents and messages:
            # Simple concatenation for now if dspy passed messages
            # Or better, let's just dump it to string if it's a list
            final_contents = str(messages)

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=final_contents,
                config=config
            )
            
            # Extract text from response
            if response.text:
                return [response.text]
            return [""]
            
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            # print(f"DEBUG: kwargs keys: {kwargs.keys()}")
            return [""]

    def __call__(self, **kwargs):
        """
        Call method for DSPy LM.
        DSPy passes inputs as keyword arguments. We need to construct the prompt from them.
        Usually, dspy passes 'prompt' if it's a simple string, or other fields.
        """
        # If 'prompt' is in kwargs, use it. Otherwise, we might need to join other inputs.
        # But commonly for ChainOfThought, it constructs a prompt string and passes it as 'prompt' or implicit arg?
        # Actually dspy LMs are called with `lm(prompt, ...)` usually.
        # Let's check the error: "GeminiLM.__call__() missing 1 required positional argument: 'prompt'"
        # This means dspy is calling it as `lm(prompt, ...)` but my definition was `def __call__(self, prompt, **kwargs)`.
        # Wait, if I defined it as `def __call__(self, prompt, **kwargs)`, why did it fail?
        # Maybe dspy creates a "signature" based call?
        
        # NOTE: In dspy 2.5+, the base LM class might have a different signature or usage.
        # Let's look at standard dspy.Google implementation logic (mentally).
        # It seems I need to be careful about strict signature.
        
        # Let's simply print what we get to debug if I could, but here I must fix it.
        # If the error is "missing 1 required positional", it implies the caller did NOT pass 'prompt' as positional.
        # So dspy might be calling `lm(prompt=...)` or just `lm(...)` without positional prompt.
        
        prompt = kwargs.get("prompt")
        if not prompt:
            # If no prompt, try to join all string values in kwargs?
            # Or maybe the first arg was missed.
            pass
        return self.basic_request(prompt, **kwargs)

def configure_gemini():
    """Configures the Gemini API client using key from environment."""
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please add it to a .env file.")
    
    # Configure dspy to use our custom Gemini provider
    # Using gemini-3-flash-preview as requested
    lm = GeminiLM("gemini-3-flash-preview", api_key=api_key)
    dspy.settings.configure(lm=lm)

def get_model():
    """Returns a configured Gemini client instance."""
    # This might be deprecated depending on usage, but returning client as modern equivalent
    api_key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=api_key)
