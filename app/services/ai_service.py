import google.generativeai as genai
from google.generativeai.types import (
    GenerationConfig,
    HarmCategory,
    HarmBlockThreshold,
)  # For safety settings and config
from fastapi import HTTPException, status
from app.core.config import settings
from typing import Optional, Dict, Any, List
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
        logger.info(prompt)
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


async def continue_writing(content: Optional[str], title: Optional[str] = None) -> str:
    """
    Continues writing the note based on existing content and title using a structured prompt.
    If content is empty, starts writing based solely on the title.
    Ensures non-conversational output.
    """
    title_for_prompt = title if title is not None else ""
    content_for_prompt = content if content is not None else ""

    # Construct the prompt using the structure we designed
    # MODIFIED PROMPT TO PREVENT QUESTIONS/CONVERSATION
    prompt = f"""You are an AI writing assistant specialized in helping users continue their notes. Your sole purpose is to provide a direct, non-interactive text continuation.

Here is the current note information provided by the user:
Note Title: {title_for_prompt}
Note Content: {content_for_prompt}

Your task is to generate a natural continuation for the Note Content.

Instructions:
1. If the Note Content is currently empty, begin writing content that is relevant to and inspired by the Note Title.
2. If the Note Content is not empty, read the Note Title and the existing Note Content. Then, continue writing naturally from the end of the existing Note Content, ensuring the new text flows seamlessly.
3. Maintain the original language used in the Note Title and Note Content.
4. Maintain the existing writing style and tone of the note (if content exists), or adopt a suitable tone based on the title (if content is empty).
5. The continuation should be relatively concise, suitable for a note-taking context. Aim for a short to moderate addition.
6. Crucially: Your output must be raw text. Do not use Markdown, rich text formatting, or any special characters beyond basic punctuation (like commas, periods, dashes '-', parentheses '()', question marks '?', exclamation points '!'). Ensure the output is plain text.
7. **Absolutely critical: Your entire output must be *only* the generated continuation text.** Do not include the Note Title, the existing Note Content, or any other text. **Specifically, do not include any questions, prompts for the user, conversational filler, introductory phrases (like "Here is a continuation:"), concluding remarks, or any other form of dialogue or interaction.** Just provide the raw text that directly continues the note.

Please generate the continuation text now based on the provided information.
"""

    generated_text = await _call_gemini_api(prompt)

    return generated_text


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


async def generate_tasks_from_title(
    title: str, language_hint: Optional[str] = None
) -> List[str]:
    """
    Generates a list of relevant task titles based on a note title.

    Args:
        title: The title of the note to generate tasks for.
        language_hint: Optional hint for the language (e.g., 'Vietnamese', 'English')

    Returns:
        A list of generated task title strings. Returns empty list on failure.
    """
    language_instruction = (
        f"Respond *only* in the *same language* as the input title (likely {language_hint})."
        if language_hint
        else "Respond *only* in the *same language* as the input title."
    )

    prompt = f"""You are an AI assistant. Your task is to brainstorm and generate a list of actionable task titles based on the following note title. Think about the steps or sub-items related to the title.

**Constraints:**
- Generate relevant, concise, and actionable task titles.
- Output *only* a plain text list, with each task title on a new line.
- Do *not* use numbers, bullets (like -, *), or any other formatting unless it's part of the task title itself.
- {language_instruction}
- Aim for a reasonable number of tasks (e.g., 3-7), but adjust based on the title's complexity.
- If the title doesn't seem actionable or is too vague for task generation, return an empty response or a single line saying "No specific tasks suggested".

**Note Title:**
---
{title}
---

**Generated Task Titles (one per line):**"""

    config = GenerationConfig(
        temperature=0.6,  # Allow some creativity for brainstorming
        # max_output_tokens=... # Set if needed, tasks are usually short
    )

    try:
        # Assuming _call_gemini_api handles errors and returns the raw text output
        generated_text = await _call_gemini_api(prompt, generation_config=config)

        if (
            not generated_text
            or "no specific tasks suggested" in generated_text.lower()
        ):
            return []

        # Parse the output: split by newline, strip whitespace, filter empty lines
        task_titles = [
            line.strip() for line in generated_text.splitlines() if line.strip()
        ]

        # Basic filter for potential refusal phrases (optional)
        task_titles = [
            t for t in task_titles if "cannot generate tasks" not in t.lower()
        ]

        return task_titles

    except Exception as e:
        logger.error(f"Error generating tasks for title '{title}': {e}", exc_info=True)
        return []  # Return empty list on error


async def summarize_task_list(tasks: List[str], title: Optional[str] = None) -> str:
    """Summarizes a list of task titles, aiming for a concise title-like summary."""
    if not tasks:
        return "Summary: No tasks found"  # Provide a default title

    title_context = f"The overall topic is: {title}\n\n" if title else ""
    task_list_str = "\n".join(f"- {task_title}" for task_title in tasks)

    # Modified prompt to encourage a title-like summary
    prompt = f"""You are an AI assistant. Create a concise summary title for the following list of tasks. Consider the main topic if provided.

**Constraints:**
- The summary should be short enough to be a task title itself.
- Capture the main essence of the tasks.
- Start the summary with "Summary: ".
- Respond *only* in the *same language* as the input tasks/title.
- Output *only* the summary title text itself.
- **Strictly avoid** Markdown formatting.

{title_context}**Task List:**
---
{task_list_str}
---

**Summary Title:**"""  # Changed from "Summary:"
    config = GenerationConfig(temperature=0.5)
    # Limit output tokens to make it more title-like if needed
    # config.max_output_tokens = 50
    summary_title = await _call_gemini_api(prompt, generation_config=config)

    # Ensure it starts with "Summary: " for consistency, or add if missing
    if not summary_title.lower().startswith("summary:"):
        summary_title = f"Summary: {summary_title}"

    return summary_title


async def generate_more_tasks(
    title: str, existing_tasks: List[str], language_hint: Optional[str] = None
) -> List[str]:
    """Generates additional tasks based on a title and existing tasks."""
    language_instruction = (
        f"Respond *only* in the *same language* as the input (likely {language_hint})."
        if language_hint
        else "Respond *only* in the *same language* as the input."
    )
    existing_tasks_str = (
        "\n".join(f"- {t}" for t in existing_tasks) if existing_tasks else "None"
    )

    prompt = f"""You are an AI assistant. Based on the note title and the existing tasks listed below, brainstorm and suggest *additional* relevant and actionable task titles.

**Constraints:**
- Generate only *new* task titles that are not already listed or slight variations.
- Output *only* a plain text list of the new task titles, each on a new line.
- Do *not* use numbers or bullets.
- {language_instruction}
- If no more relevant tasks come to mind, return an empty response.

**Note Title:**
---
{title}
---

**Existing Tasks:**
---
{existing_tasks_str}
---

**Additional Task Titles (one per line):**"""
    config = GenerationConfig(temperature=0.7)

    try:
        generated_text = await _call_gemini_api(prompt, generation_config=config)
        if not generated_text:
            return []
        new_task_titles = [
            line.strip() for line in generated_text.splitlines() if line.strip()
        ]
        # Filter out potential duplicates (case-insensitive) just in case
        existing_lower = {t.lower() for t in existing_tasks}
        new_task_titles = [
            t for t in new_task_titles if t.lower() not in existing_lower
        ]
        return new_task_titles
    except Exception as e:
        logger.error(
            f"Error generating more tasks for title '{title}': {e}", exc_info=True
        )
        return []
