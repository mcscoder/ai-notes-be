# In your AI endpoints file (e.g., app/api/v1/endpoints/ai.py)

from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from sqlmodel import Session
from typing import List, Any
import asyncio

from app.core.deps import get_current_user
from app.crud import v1
from app.db import session
from app.models import user as UserModel, note as NoteModel, task as TaskModel
from app.schemas import note as NoteSchema, task as TaskSchema, common as CommonSchema
from app.services import ai_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Helper Functions (Keep as previously defined) ---
# _generate_and_create_tasks
# _apply_ai_to_existing_tasks
# (Include the code for these helpers from the previous responses here)
async def _generate_and_create_tasks(
    note: NoteModel.Note,
    current_user: UserModel.User,
    session: Session,
) -> bool:
    """Generates tasks via AI and saves them. Returns True if tasks were created."""
    logger.info(
        f"Note {note.id} is task-based but has no tasks. Attempting generation."
    )
    language_hint = None  # Add language detection if possible
    generated_titles = await ai_service.generate_tasks_from_title(
        note.title, language_hint
    )

    if not generated_titles:
        logger.warning(
            f"AI did not generate any tasks for note {note.id} (Title: {note.title})."
        )
        return False

    logger.info(f"Generated {len(generated_titles)} task titles for note {note.id}.")
    try:
        created_count = 0
        for task_title in generated_titles:
            if task_title:
                task_create_data = TaskSchema.TaskCreate(title=task_title)
                # Assuming create_task handles adding task to note and commits/adds to session
                created_task = v1.note.create_task(
                    note.id, task_create_data, current_user, session
                )
                if created_task:
                    created_count += 1
                else:
                    logger.error(
                        f"Failed to create task '{task_title}' for note {note.id}"
                    )
        logger.info(f"Successfully created {created_count} tasks for note {note.id}.")
        # Ensure changes are flushed to session before refresh if create_task doesn't commit
        session.flush()
        return created_count > 0
    except Exception as e:
        logger.error(
            f"Error saving generated tasks for note {note.id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to save generated tasks.")


async def _apply_ai_to_existing_tasks(
    ai_function: callable,
    note: NoteModel.Note,
    session: Session,
    is_sub_task_structure: bool = False,
    **kwargs,  # Pass extra args like style
):
    """Applies an AI function to the titles of existing tasks/subtasks concurrently."""
    tasks_to_process = []
    # Ensure tasks are loaded before processing
    if not hasattr(note, "tasks") or note.tasks is None:
        logger.debug(
            f"Explicitly refreshing tasks for note {note.id} before AI application."
        )
        session.refresh(note, attribute_names=["tasks"])

    if is_sub_task_structure:
        # Also ensure sub-tasks are loaded if needed (might require deeper refresh or careful loading)
        for parent_task in note.tasks:
            # Explicitly refresh sub-tasks for the parent task if necessary
            if not hasattr(parent_task, "tasks") or parent_task.tasks is None:
                logger.debug(
                    f"Explicitly refreshing sub-tasks for parent task {parent_task.id}."
                )
                session.refresh(parent_task, attribute_names=["tasks"])
            if parent_task.tasks:
                tasks_to_process.extend(
                    [(sub_task, parent_task.title) for sub_task in parent_task.tasks]
                )
    else:
        # Ensure tasks relationship is loaded for the note
        if not hasattr(note, "tasks") or note.tasks is None:
            session.refresh(note, attribute_names=["tasks"])
        if note.tasks:  # Check if tasks exist after refresh
            tasks_to_process.extend([(task, note.title) for task in note.tasks])

    if not tasks_to_process:
        logger.info(f"No existing tasks found to apply AI for note {note.id}.")
        return  # Nothing to do

    logger.info(
        f"Applying AI function '{ai_function.__name__}' to {len(tasks_to_process)} tasks/subtasks for note {note.id}."
    )

    update_coroutines = []
    for task, context_title in tasks_to_process:

        async def update_single_task(task_to_update: TaskModel.Task, context: str):
            try:
                # Pass kwargs (like style) to the AI function
                modified_title = await ai_function(
                    task_to_update.title, context, **kwargs
                )
                if modified_title != task_to_update.title:
                    task_update_data = TaskSchema.TaskUpdate(title=modified_title)
                    # Assuming update_task handles session/commit logic correctly
                    updated = v1.note.update_task(
                        task_to_update.id, task_update_data, session
                    )
                    if not updated:
                        logger.warning(
                            f"CRUD function failed to update task {task_to_update.id} after AI processing."
                        )
            except Exception as e:
                logger.error(
                    f"Error applying AI or updating task {task_to_update.id}: {e}",
                    exc_info=True,
                )

        update_coroutines.append(update_single_task(task, context_title))

    results = await asyncio.gather(*update_coroutines, return_exceptions=True)
    # Log any exceptions gathered
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            task_id = tasks_to_process[i][0].id  # Safely get task id
            logger.error(f"Exception processing task {task_id} during gather: {result}")
    # Ensure changes within the loop are flushed before the final note refresh
    session.flush()


# --- Unified API Endpoints (Including Save for Summarize) ---


# Keep /format, /cleanup, /refine, /polish, /continue as in the previous response
# (Include their code here)
@router.post("/{note_id}/format", response_model=NoteSchema.NoteRead)
async def format_note(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    try:
        if note.type in [1, 4]:  # Content-based note
            if note.content is not None:  # Check if content exists
                modified_content = await ai_service.format_content(
                    note.content, note.title
                )
                if modified_content != note.content:
                    note_update_data = NoteSchema.NoteUpdate(content=modified_content)
                    v1.note.update_note(
                        note.id, note_update_data, current_user, session
                    )
                    session.flush()  # Ensure change is flushed before refresh
            else:
                logger.info(f"Note {note.id} has no content to format.")
        else:  # Task-based note
            logger.info(
                f"Format requested for task-based note {note.id}. No action taken on tasks for 'format'."
            )

    except Exception as e:
        logger.error(
            f"Error during format processing for note {note.id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to process format request.")

    logger.debug(f"Refreshing note {note.id} before returning.")
    session.refresh(note)
    return note


@router.post("/{note_id}/cleanup", response_model=NoteSchema.NoteRead)
async def cleanup_note_or_tasks(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    try:
        if note.type in [1, 4]:  # Content-based
            if note.content is not None:
                modified_content = await ai_service.cleanup_content(
                    note.content, note.title
                )
                if modified_content != note.content:
                    note_update_data = NoteSchema.NoteUpdate(content=modified_content)
                    v1.note.update_note(
                        note.id, note_update_data, current_user, session
                    )
                    session.flush()
            else:
                logger.info(f"Note {note.id} has no content to clean up.")
        else:  # Task-based
            if not hasattr(note, "tasks") or note.tasks is None:
                session.refresh(note, attribute_names=["tasks"])
            tasks_exist = bool(note.tasks)
            if not tasks_exist:
                await _generate_and_create_tasks(note, current_user, session)
            else:
                is_sub_task = note.type == 3
                await _apply_ai_to_existing_tasks(
                    ai_service.cleanup_content, note, session, is_sub_task
                )

    except Exception as e:
        logger.error(f"Error during cleanup for note {note.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to process cleanup request."
        )

    logger.debug(f"Refreshing note {note.id} before returning.")
    session.refresh(note)
    return note


@router.post("/{note_id}/refine", response_model=NoteSchema.NoteRead)
async def refine_note_or_tasks(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
    options: CommonSchema.AiActionRequest = Body(
        default=CommonSchema.AiActionRequest()
    ),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    try:
        if note.type in [1, 4]:
            if note.content is not None:
                modified_content = await ai_service.refine_content(
                    note.content, note.title, style=options.style
                )
                if modified_content != note.content:
                    note_update_data = NoteSchema.NoteUpdate(content=modified_content)
                    v1.note.update_note(
                        note.id, note_update_data, current_user, session
                    )
                    session.flush()
            else:
                logger.info(f"Note {note.id} has no content to refine.")
        else:
            if not hasattr(note, "tasks") or note.tasks is None:
                session.refresh(note, attribute_names=["tasks"])
            tasks_exist = bool(note.tasks)
            if not tasks_exist:
                await _generate_and_create_tasks(note, current_user, session)
            else:
                is_sub_task = note.type == 3
                await _apply_ai_to_existing_tasks(
                    ai_service.refine_content,
                    note,
                    session,
                    is_sub_task,
                    style=options.style,
                )
    except Exception as e:
        logger.error(f"Error during refine for note {note.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process refine request.")

    logger.debug(f"Refreshing note {note.id} before returning.")
    session.refresh(note)
    return note


@router.post("/{note_id}/polish", response_model=NoteSchema.NoteRead)
async def polish_note_or_tasks(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    try:
        if note.type in [1, 4]:
            if note.content is not None:
                modified_content = await ai_service.polish_content(
                    note.content, note.title
                )
                if modified_content != note.content:
                    note_update_data = NoteSchema.NoteUpdate(content=modified_content)
                    v1.note.update_note(
                        note.id, note_update_data, current_user, session
                    )
                    session.flush()
            else:
                logger.info(f"Note {note.id} has no content to polish.")
        else:
            if not hasattr(note, "tasks") or note.tasks is None:
                session.refresh(note, attribute_names=["tasks"])
            tasks_exist = bool(note.tasks)
            if not tasks_exist:
                await _generate_and_create_tasks(note, current_user, session)
            else:
                is_sub_task = note.type == 3
                await _apply_ai_to_existing_tasks(
                    ai_service.polish_content, note, session, is_sub_task
                )
    except Exception as e:
        logger.error(f"Error during polish for note {note.id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process polish request.")

    logger.debug(f"Refreshing note {note.id} before returning.")
    session.refresh(note)
    return note


@router.post("/{note_id}/continue", response_model=NoteSchema.NoteRead)
async def continue_note_or_tasks(
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
    options: CommonSchema.AiActionRequest = Body(
        default=CommonSchema.AiActionRequest()
    ),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    try:
        if note.type in [1, 4]:  # Content-based
            # --- Handle None or empty content ---
            # Pass note.content directly (which might be None) to the service function
            # The service function is now designed to handle None/empty content
            generated_text = await ai_service.continue_writing(
                note.content,  # Pass potentially None content
                note.title,
                max_tokens=options.max_tokens,
            )

            if generated_text:  # Only proceed if AI generated something
                original_content = (
                    note.content if note.content else ""
                )  # Treat None as empty string for appending
                # Determine separator: Add if original content existed, otherwise no separator needed.
                separator = "\n\n" if original_content else ""
                new_content = original_content + separator + generated_text

                # Update the note
                note_update_data = NoteSchema.NoteUpdate(content=new_content)
                v1.note.update_note(note.id, note_update_data, current_user, session)
                session.flush()
                logger.info(
                    f"Successfully updated content for note {note.id} via continue writing."
                )
            else:
                logger.info(
                    f"AI did not generate text for continue writing on note {note.id}."
                )

        else:  # Task-based: Generate *more* tasks (Logic remains the same)
            if not hasattr(note, "tasks") or note.tasks is None:
                session.refresh(note, attribute_names=["tasks"])
            existing_task_titles = [task.title for task in note.tasks if task.title]
            language_hint = None
            logger.info(
                f"Continue writing requested for task note {note.id}. Generating more tasks."
            )
            new_task_titles = await ai_service.generate_more_tasks(
                note.title, existing_task_titles, language_hint
            )

            if new_task_titles:
                logger.info(
                    f"Generated {len(new_task_titles)} additional tasks for note {note.id}."
                )
                created_count = 0
                for task_title in new_task_titles:
                    if task_title:
                        task_create_data = TaskSchema.TaskCreate(title=task_title)
                        created = v1.note.create_task(
                            note.id, task_create_data, current_user, session
                        )
                        if created:
                            created_count += 1
                logger.info(
                    f"Successfully added {created_count} tasks for note {note.id}."
                )
                session.flush()
            else:
                logger.info(
                    f"AI did not generate any additional tasks for note {note.id}."
                )

    except Exception as e:
        logger.error(
            f"Error during continue writing for note {note.id}: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to process continue writing request."
        )

    logger.debug(f"Refreshing note {note.id} before returning.")
    session.refresh(note)  # Refresh to get potentially updated content or new tasks
    return note


# --- MODIFIED Summarize Endpoint ---
@router.post(
    "/{note_id}/summarize", response_model=NoteSchema.NoteRead
)  # RESPONSE MODEL IS NoteRead
async def summarize_and_save(  # Renamed function
    note_id: int,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
    options: CommonSchema.AiActionRequest = Body(
        default=CommonSchema.AiActionRequest()
    ),
):
    note = v1.note.get_note_by_id(note_id, current_user, session)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    summary_text = ""  # Initialize summary text

    try:
        if note.type in [1, 4]:  # Content-based: Append summary to content
            if note.content:
                generated_summary = await ai_service.summarize_content(
                    note.content, note.title, max_length=options.max_length
                )
                if generated_summary:
                    summary_text = generated_summary  # Keep track for logging maybe
                    # Append the summary
                    separator = "\n\n---\nSummary:\n"  # Define a clear separator
                    new_content = note.content + separator + generated_summary
                    note_update_data = NoteSchema.NoteUpdate(content=new_content)
                    v1.note.update_note(
                        note.id, note_update_data, current_user, session
                    )
                    session.flush()  # Flush update
                    logger.info(f"Appended summary to content for note {note.id}.")
                else:
                    logger.info(f"AI did not generate a summary for note {note.id}.")
            else:
                logger.info("Note has no content to summarize.")

        else:  # Task-based: Create a new task with the summary as its title
            if not hasattr(note, "tasks") or note.tasks is None:
                session.refresh(note, attribute_names=["tasks"])

            task_titles = []
            is_sub_task = note.type == 3
            if is_sub_task:
                for parent_task in note.tasks:
                    if not hasattr(parent_task, "tasks") or parent_task.tasks is None:
                        session.refresh(parent_task, attribute_names=["tasks"])
                    if parent_task.tasks:
                        task_titles.extend(
                            [
                                f"{parent_task.title}: {sub.title}"
                                for sub in parent_task.tasks
                                if sub.title
                            ]
                        )
            else:
                task_titles = [task.title for task in note.tasks if task.title]

            if task_titles:
                # Generate a concise summary suitable for a task title
                summary_task_title = await ai_service.summarize_task_list(
                    task_titles, note.title
                )
                if summary_task_title and not summary_task_title.lower().startswith(
                    "summary: no tasks"
                ):
                    summary_text = summary_task_title  # Keep track for logging
                    # Create the new summary task
                    task_create_data = TaskSchema.TaskCreate(
                        title=summary_task_title, is_finished=True
                    )  # Mark summary task as finished? Optional.
                    created = v1.note.create_task(
                        note.id, task_create_data, current_user, session
                    )
                    if created:
                        logger.info(
                            f"Created summary task for note {note.id} with title: '{summary_task_title}'"
                        )
                        session.flush()  # Flush creation
                    else:
                        logger.error(
                            f"Failed to create summary task for note {note.id}"
                        )
                else:
                    logger.info(
                        f"AI did not generate a valid summary task title for note {note.id}."
                    )
            else:
                logger.info("Note has no tasks to summarize.")

    except Exception as e:
        logger.error(
            f"Error during summarize and save for note {note.id}: {e}", exc_info=True
        )
        # Allow proceeding to refresh/return, but the summary operation might have failed
        # Or raise HTTPException(status_code=500, detail="Failed to process summary request.")

    # Refresh and return the note - including the appended summary or new task
    logger.debug(f"Refreshing note {note.id} before returning after summarize.")
    session.refresh(note)
    return note
