#!/usr/bin/env python3

import re
import sys

from action_contract import (
    ActionContractError,
    DESKTOP_CLI,
    create_action_request,
)
from policy_enforced_tier_zero_action import execute_action
from intent_engine import build_trigger_pairs
from selection import get_selection_key
from skills import (
    change_due_date,
    complete_task,
    create_category,
    delete_task,
    edit_task,
    filter_tasks,
    grocery,
    morning_brief,
    move_task,
    read_groceries,
    read_tasks,
    recall_notes,
    remember,
    show_due_tasks,
    tasks,
)


READ_ONLY_FLAG = "--read-only"
INTERFACE_FLAG = "--interface"
READ_ONLY_DENIED_RESPONSE = (
    "Changes are disabled for this interface until "
    "authorization is available."
)
ACTION_CONTRACT_DENIED_RESPONSE = (
    "That read request could not be safely completed."
)

SKILLS = [
    change_due_date,
    complete_task,
    create_category,
    delete_task,
    edit_task,
    filter_tasks,
    grocery,
    morning_brief,
    move_task,
    read_groceries,
    read_tasks,
    recall_notes,
    remember,
    show_due_tasks,
    tasks,
]


def route_pending_selection(question: str) -> bool:
    selection_key = get_selection_key()

    if not selection_key:
        return False

    answer = question.strip().lower()

    if selection_key == "remember_note":
        # Route every response. The remember skill owns exact
        # confirmation classification and fail-closed cleanup.
        pass

    elif selection_key == "create_task_priority":
        if not re.fullmatch(
            r"(?:critical|high(?: priority)?|"
            r"normal(?: priority)?|low(?: priority)?)",
            answer,
        ):
            return False

    elif selection_key == "delete_task":
        if not re.fullmatch(
            r"(?:yes|yeah|yep|confirm|no|nope|cancel|"
            r"task\s+(?:one|two|three|four|five))",
            answer,
            flags=re.IGNORECASE,
        ):
            return False

    elif not re.fullmatch(
        r"task\s+(?:one|two|three|four|five)",
        answer,
        flags=re.IGNORECASE,
    ):
        return False

    for skill in SKILLS:
        if getattr(skill, "SELECTION_KEY", None) != selection_key:
            continue

        response = skill.handle("", answer)
        print(response)
        return True

    return False


def route_command(
    question: str,
    *,
    read_only: bool = False,
    interface: str = DESKTOP_CLI,
) -> bool:
    if not read_only and route_pending_selection(question):
        return True

    lower_question = question.lower()

    for skill in SKILLS:
        for spoken_trigger, canonical_trigger in build_trigger_pairs(skill):
            if spoken_trigger not in lower_question:
                continue

            start = lower_question.index(spoken_trigger)
            text = question[start + len(spoken_trigger):]
            text = text.lstrip(" ,.:;?-").strip()

            if (
                read_only
                and not getattr(skill, "READ_ONLY", False)
            ):
                print(READ_ONLY_DENIED_RESPONSE)
                return True

            if skill is read_tasks:
                try:
                    request = create_action_request(
                        "tasks.read",
                        interface=interface,
                    )
                    response = execute_action(request)
                except ActionContractError:
                    print(ACTION_CONTRACT_DENIED_RESPONSE)
                    return True
            elif getattr(skill, "USES_TRIGGER", False):
                response = skill.handle(text, canonical_trigger)
            else:
                response = skill.handle(text)

            print(response)
            return True

    return False


if __name__ == "__main__":
    arguments = sys.argv[1:]
    interface = DESKTOP_CLI
    read_only = False

    if arguments and arguments[0] == READ_ONLY_FLAG:
        read_only = True
        arguments = arguments[1:]

    if arguments and arguments[0] == INTERFACE_FLAG:
        if len(arguments) < 2:
            print("No interface provided.")
            sys.exit(1)

        interface = arguments[1]
        arguments = arguments[2:]

    question = " ".join(arguments).strip()

    if not question:
        if not read_only and route_pending_selection(""):
            sys.exit(0)

        print("No command provided.")
        sys.exit(1)

    sys.exit(
        0
        if route_command(
            question,
            read_only=read_only,
            interface=interface,
        )
        else 2
    )
