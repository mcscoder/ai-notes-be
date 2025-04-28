import google.generativeai as genai
from google.generativeai.types import (
    GenerationConfig,
    HarmCategory,
    HarmBlockThreshold,
)  # For safety settings and config
from fastapi import HTTPException, status
from app.core.config import settings
from typing import Optional, Dict, Any
import logging  # Import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the Gemini client
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")
    # Decide if you want the app to fail startup or handle this later
    # raise RuntimeError("Gemini API key configuration failed") from e


# --- Central Gemini API Call Helper ---
async def _call_gemini_api(
    prompt: str,
    generation_config: Optional[GenerationConfig] = None,
    safety_settings: Optional[Dict[HarmCategory, HarmBlockThreshold]] = None,
) -> str:
    """
    Helper function to call the Gemini API, handle errors, and extract text.

    Args:
        prompt: The complete prompt string for the Gemini model.
        generation_config: Optional GenerationConfig for temperature, max tokens etc.
        safety_settings: Optional safety settings dictionary.

    Returns:
        The generated text content from the model.

    Raises:
        HTTPException: If the API call fails, is blocked, or returns unexpected data.
    """
    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

        # Default safety settings (adjust as needed)
        if safety_settings is None:
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }

        logger.info(f"Calling Gemini model {settings.GEMINI_MODEL_NAME}")
        # Use generate_content_async for async operation if available and needed,
        # otherwise, run the sync version in a threadpool if it blocks heavily.
        # For simplicity here, using the sync version directly.
        # Consider using asyncio.to_thread for long calls if needed.
        response = model.generate_content(
            prompt, generation_config=generation_config, safety_settings=safety_settings
        )
        logger.info("Gemini response received")

        # --- Crucial Error and Safety Handling ---
        # 1. Check for blocking reasons first
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason.name
            logger.warning(f"Gemini request blocked due to: {block_reason}")
            # Provide a more user-friendly message if possible
            detail_msg = f"Request blocked by safety filter: {block_reason}. Please revise your input."
            if block_reason == "SAFETY":
                detail_msg = "Request blocked due to safety concerns in the prompt or potential output. Please revise your input."
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=detail_msg
            )

        # 2. Check if candidates exist and have content
        if not response.candidates:
            logger.error("Gemini response missing candidates.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service returned no response candidates.",
            )

        # 3. Access the text, handling potential finish reasons and missing parts
        try:
            # Check finish reason if needed - e.g., 'MAX_TOKENS' might mean incomplete output
            finish_reason = (
                response.candidates[0].finish_reason.name
                if response.candidates[0].finish_reason
                else "UNKNOWN"
            )
            if finish_reason not in ["STOP", "UNKNOWN"]:  # Allow UNKNOWN for now
                logger.warning(f"Gemini generation finished due to: {finish_reason}")
                # Decide if this is an error - MAX_TOKENS might be acceptable but truncated

            # Get text, ensuring parts exist
            if (
                not response.candidates[0].content
                or not response.candidates[0].content.parts
            ):
                logger.error("Gemini response candidate missing content or parts.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI service returned empty content.",
                )

            generated_text = response.text  # response.text is a convenience accessor

            if not generated_text:
                logger.error("Gemini response.text is empty.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="AI service returned empty text.",
                )

            return generated_text.strip()

        except (AttributeError, IndexError, ValueError) as e:
            logger.error(
                f"Error parsing Gemini response: {e}\nResponse: {response}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse AI service response.",
            )

    except Exception as e:
        # Catch other potential errors during API call
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        # Check for specific google api core exceptions if needed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service communication error: {e}",
        )


# --- Specific AI Feature Implementations ---


async def format_content(content: str, title: Optional[str] = None) -> str:
    """Formats note content using standard punctuation, using title for context."""
    title_context = f"Note Title: {title}\n\n" if title else ""  # Add title if present
    prompt = f"""You are an AI assistant. Your task is to reformat the following text for better readability and structure suitable for a *plain text editor*. Use the note title below for context if helpful. Use standard punctuation, symbols, and layout techniques like:
- Hyphens (-) or asterisks (*) for list items.
- Indentation (using spaces) to show structure or hierarchy.
- Blank lines to separate paragraphs or sections.
- Consistent use of punctuation (periods, commas, etc.).

**Constraints:**
- Organize related ideas logically based on the title and content.
- Do *not* change the core meaning or add new information.
- Respond *only* in the *same language* as the input text.
- Output *only* the formatted text, without any preamble or explanation.
- **Strictly avoid** Markdown formatting (like ##, **, _, ```).

{title_context}**Input Text:**
---
{content}
---

**Formatted Output:**"""
    config = GenerationConfig(temperature=0.3)
    return await _call_gemini_api(prompt, generation_config=config)


async def cleanup_content(content: str, title: Optional[str] = None) -> str:
    """Cleans up text (grammar, spelling, redundancy), using title for context."""
    title_context = f"Note Title: {title}\n\n" if title else ""
    prompt = f"""You are an AI assistant. Your task is to clean up the following text. Use the note title for context.
- Correct spelling and grammar errors.
- Remove redundant words or phrases.
- Improve clarity and conciseness.
- Ensure sentences flow well.

**Constraints:**
- Do *not* change the core meaning of the text.
- Respond *only* in the *same language* as the input text.
- Output *only* the cleaned-up text, without any preamble or explanation.
- **Strictly avoid** Markdown formatting (like ##, **, _, ```).

{title_context}**Input Text:**
---
{content}
---

**Cleaned Up Output:**"""
    config = GenerationConfig(temperature=0.5)
    return await _call_gemini_api(prompt, generation_config=config)


async def refine_content(
    content: str, title: Optional[str] = None, style: Optional[str] = None
) -> str:
    """Refines writing style, using title for context."""
    title_context = f"Note Title: {title}\n\n" if title else ""
    style_instruction = (
        f"aiming for a '{style}' style (e.g., professional, casual, formal, engaging)"
        if style
        else "making it more expressive and fluent"
    )
    prompt = f"""You are an AI assistant. Your task is to refine the writing style of the following text, {style_instruction}, using the note title for overall context.
- Improve word choice.
- Enhance sentence structure and flow.
- Make the language more engaging or appropriate for the desired style and topic (indicated by the title).

**Constraints:**
- Do *not* change the core meaning significantly.
- Respond *only* in the *same language* as the input text.
- Output *only* the refined text, without any preamble or explanation.
- **Strictly avoid** Markdown formatting (like ##, **, _, ```).

{title_context}**Input Text:**
---
{content}
---

**Refined Output:**"""
    config = GenerationConfig(temperature=0.7)
    return await _call_gemini_api(prompt, generation_config=config)


async def continue_writing(
    content: str, title: Optional[str] = None, max_tokens: Optional[int] = 150
) -> str:
    """Continues writing, using title for topic guidance."""
    title_context = f"Note Title: {title}\n\n" if title else ""
    estimated_max_tokens = int(max_tokens / 0.7) if max_tokens else 200
    prompt = f"""You are an AI assistant. Your task is to continue writing the text below naturally and coherently, staying on the topic indicated by the title and existing content. Maintain the existing tone and style.

**Constraints:**
- Generate approximately {max_tokens} words (or fill the token limit).
- Start the continuation directly, *without* repeating the input text.
- Respond *only* in the *same language* as the input text.
- Output *only* the continued text.
- **Strictly avoid** Markdown formatting (like ##, **, _, ```).

{title_context}**Input Text (Continue from here):**
---
{content}
---

**Continuation:**"""
    config = GenerationConfig(temperature=0.7, max_output_tokens=estimated_max_tokens)
    return await _call_gemini_api(prompt, generation_config=config)


async def polish_content(content: str, title: Optional[str] = None) -> str:
    """Polishes text subtly, using title for context."""
    title_context = f"Note Title: {title}\n\n" if title else ""
    prompt = f"""You are an AI assistant. Your task is to review and gently polish the following text, using the title for context.
- Improve the flow and readability.
- Enhance clarity without changing meaning.
- Correct any subtle grammar or punctuation issues.
- Ensure a smooth and consistent tone relevant to the topic.
- Make only necessary, subtle improvements. Do *not* rewrite significantly.

**Constraints:**
- Do *not* change the core meaning or style drastically.
- Respond *only* in the *same language* as the input text.
- Output *only* the polished text, without any preamble or explanation.
- **Strictly avoid** Markdown formatting (like ##, **, _, ```).

{title_context}**Input Text:**
---
{content}
---

**Polished Output:**"""
    config = GenerationConfig(temperature=0.4)
    return await _call_gemini_api(prompt, generation_config=config)


async def summarize_content(
    content: str, title: Optional[str] = None, max_length: Optional[int] = 100
) -> str:
    """Summarizes text, using title for topic focus."""
    title_context = f"Note Title: {title}\n\n" if title else ""
    length_instruction = (
        f"Aim for a concise summary, ideally around {max_length} words."
        if max_length
        else "Provide a concise summary of the main points."
    )
    estimated_max_tokens = int(max_length * 1.8) if max_length else 250
    prompt = f"""You are an AI assistant. Your task is to summarize the main points of the following text, considering the note title for the main topic. {length_instruction}

**Constraints:**
- Capture the essential information accurately, focusing on the topic indicated by the title.
- Respond *only* in the *same language* as the input text.
- Output *only* the summary text itself, without any preamble like "Here is a summary:".
- **Strictly avoid** Markdown formatting (like ##, **, _, ```).

{title_context}**Input Text:**
---
{content}
---

**Summary:**"""
    config = GenerationConfig(temperature=0.5, max_output_tokens=estimated_max_tokens)
    return await _call_gemini_api(prompt, generation_config=config)
