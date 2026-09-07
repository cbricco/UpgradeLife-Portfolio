#!/usr/bin/env python3

import hashlib
import json

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable

import session_context
from skills import read_tasks


TIER_0 = 0
TIER_1 = 1

_KNOWN_RISK_TIERS = frozenset({TIER_0, TIER_1})

DESKTOP_CLI = "desktop_cli"
DESKTOP_VOICE = "desktop_voice"
BROWSER = "browser"

_VALID_INTERFACES = frozenset(
    {
        DESKTOP_CLI,
        DESKTOP_VOICE,
        BROWSER,
    }
)


class ActionContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ActionRequest:
    action: str
    record_type: str
    target: str
    arguments: tuple[tuple[str, str], ...]
    risk_tier: int
    session_id: str
    interface: str


def request_hash(request: ActionRequest) -> str:
    validated_request, _ = _validate_request_integrity(request)

    source = json.dumps(
        {
            "version": 1,
            "action": validated_request.action,
            "record_type": validated_request.record_type,
            "target": validated_request.target,
            "arguments": validated_request.arguments,
            "risk_tier": validated_request.risk_tier,
            "interface": validated_request.interface,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    return hashlib.sha256(source).hexdigest()


@dataclass(frozen=True, slots=True)
class _ActionSpecification:
    record_type: str
    target: str
    normalize_arguments: Callable[
        [object],
        tuple[tuple[str, str], ...],
    ]
    risk_tier: int
    execute: Callable[[], str] | None


def _execute_tasks_read() -> str:
    return read_tasks.handle("")


def _normalize_tasks_read_arguments(
    arguments: object,
) -> tuple[tuple[str, str], ...]:
    if arguments is None:
        return ()

    if type(arguments) is not dict or arguments:
        raise ActionContractError(
            "Invalid arguments for tasks.read."
        )

    return ()


_LINE_SEPARATOR_CHARACTERS = frozenset(
    {
        "\n",
        "\r",
        "\v",
        "\f",
        "\x1c",
        "\x1d",
        "\x1e",
        "\x85",
        "\u2028",
        "\u2029",
    }
)


def _normalize_groceries_add_arguments(
    arguments: object,
) -> tuple[tuple[str, str], ...]:
    if type(arguments) is not dict or len(arguments) != 1:
        raise ActionContractError(
            "Invalid arguments for groceries.add."
        )

    key = next(iter(arguments))
    if type(key) is not str or key != "item":
        raise ActionContractError(
            "Invalid arguments for groceries.add."
        )

    item = arguments["item"]
    if type(item) is not str:
        raise ActionContractError(
            "Invalid item for groceries.add."
        )

    if any(
        character in _LINE_SEPARATOR_CHARACTERS
        for character in item
    ):
        raise ActionContractError(
            "Invalid item for groceries.add."
        )

    normalized_item = item.strip()
    if not normalized_item:
        raise ActionContractError(
            "Invalid item for groceries.add."
        )

    return (("item", normalized_item),)


_ACTION_REGISTRY = MappingProxyType(
    {
        "tasks.read": _ActionSpecification(
            record_type="task",
            target="tasks",
            normalize_arguments=_normalize_tasks_read_arguments,
            risk_tier=TIER_0,
            execute=_execute_tasks_read,
        ),
        "groceries.add": _ActionSpecification(
            record_type="grocery",
            target="grocery_list",
            normalize_arguments=_normalize_groceries_add_arguments,
            risk_tier=TIER_1,
            execute=None,
        ),
    }
)

_REVIEWED_ARGUMENT_NORMALIZERS = MappingProxyType(
    {
        "tasks.read": _normalize_tasks_read_arguments,
        "groceries.add": _normalize_groceries_add_arguments,
    }
)

_REVIEWED_TIER_0_ADAPTERS = MappingProxyType(
    {
        "tasks.read": _execute_tasks_read,
    }
)


def _require_exact_string(
    value: object,
    error_message: str,
) -> str:
    if type(value) is not str:
        raise ActionContractError(error_message)

    return value


def _get_action_specification(
    action: object,
) -> _ActionSpecification:
    action_name = _require_exact_string(
        action,
        "Invalid action.",
    )
    specification = _ACTION_REGISTRY.get(action_name)

    if specification is None:
        raise ActionContractError("Unknown action.")

    return _validate_action_specification(
        action_name,
        specification,
    )


def _validate_action_specification(
    action: str,
    specification: object,
) -> _ActionSpecification:
    if type(specification) is not _ActionSpecification:
        raise ActionContractError("Invalid action specification.")

    if (
        type(specification.record_type) is not str
        or not specification.record_type
        or type(specification.target) is not str
        or not specification.target
        or not callable(specification.normalize_arguments)
        or type(specification.risk_tier) is not int
        or specification.risk_tier not in _KNOWN_RISK_TIERS
    ):
        raise ActionContractError("Invalid action specification.")

    reviewed_normalizer = _REVIEWED_ARGUMENT_NORMALIZERS.get(action)
    if specification.normalize_arguments is not reviewed_normalizer:
        raise ActionContractError("Invalid action argument normalizer.")

    reviewed_adapter = _REVIEWED_TIER_0_ADAPTERS.get(action)
    if specification.risk_tier == TIER_0:
        if (
            reviewed_adapter is None
            or specification.execute is not reviewed_adapter
        ):
            raise ActionContractError("Invalid Tier 0 execution adapter.")
    elif specification.execute is not None:
        raise ActionContractError(
            "Tier 1 actions must not have an execution adapter."
        )

    return specification


def _validate_request_integrity(
    request: ActionRequest,
) -> tuple[ActionRequest, _ActionSpecification]:
    if type(request) is not ActionRequest:
        raise ActionContractError("Invalid action request.")

    specification = _get_action_specification(request.action)

    _require_exact_string(
        request.record_type,
        "Invalid record type.",
    )
    _require_exact_string(
        request.target,
        "Invalid target.",
    )
    _require_exact_string(
        request.session_id,
        "Invalid action session.",
    )
    _require_exact_string(
        request.interface,
        "Invalid interface provenance.",
    )

    if request.record_type != specification.record_type:
        raise ActionContractError("Invalid record type.")

    if request.target != specification.target:
        raise ActionContractError("Invalid target.")

    if type(request.arguments) is not tuple:
        raise ActionContractError("Invalid action arguments.")

    argument_dict: dict[str, str] = {}
    for argument in request.arguments:
        if (
            type(argument) is not tuple
            or len(argument) != 2
            or type(argument[0]) is not str
            or type(argument[1]) is not str
            or argument[0] in argument_dict
        ):
            raise ActionContractError("Invalid action arguments.")
        argument_dict[argument[0]] = argument[1]

    try:
        canonical_arguments = specification.normalize_arguments(
            argument_dict
        )
    except ActionContractError:
        raise ActionContractError(
            "Invalid action arguments."
        ) from None

    if request.arguments != canonical_arguments:
        raise ActionContractError("Invalid action arguments.")

    if (
        type(request.risk_tier) is not int
        or request.risk_tier != specification.risk_tier
    ):
        raise ActionContractError("Invalid risk tier.")

    if request.interface not in _VALID_INTERFACES:
        raise ActionContractError("Invalid interface provenance.")

    if not session_context.is_valid_session_id(request.session_id):
        raise ActionContractError("Invalid action session.")

    return request, specification


def _validate_request(
    request: ActionRequest,
    current_session_id: object,
) -> tuple[ActionRequest, _ActionSpecification]:
    validated_request, specification = _validate_request_integrity(request)

    if type(current_session_id) is not str:
        raise ActionContractError("No valid current session.")

    if not session_context.is_valid_session_id(current_session_id):
        raise ActionContractError("No valid current session.")

    if validated_request.session_id != current_session_id:
        raise ActionContractError("Action session does not match.")

    return validated_request, specification


def create_action_request(
    action: str,
    *,
    interface: str,
    arguments: object = None,
) -> ActionRequest:
    specification = _get_action_specification(action)
    normalized_arguments = specification.normalize_arguments(arguments)
    _require_exact_string(
        interface,
        "Invalid interface provenance.",
    )

    current_session_id = session_context.get_session_id()

    request = ActionRequest(
        action=action,
        record_type=specification.record_type,
        target=specification.target,
        arguments=normalized_arguments,
        risk_tier=specification.risk_tier,
        session_id=current_session_id,
        interface=interface,
    )

    return _validate_request(request, current_session_id)[0]


def validate_action_request(request: ActionRequest) -> ActionRequest:
    return _validate_request(
        request,
        session_context.get_session_id(),
    )[0]


def _execute_reviewed_tier_zero_action(request: ActionRequest) -> str:
    validated_request, specification = _validate_request(
        request,
        session_context.get_session_id(),
    )

    if validated_request.risk_tier != TIER_0:
        raise ActionContractError(
            "Only Tier 0 actions may execute."
        )

    reviewed_adapter = _REVIEWED_TIER_0_ADAPTERS.get(
        validated_request.action
    )
    if (
        specification.execute is None
        or specification.execute is not reviewed_adapter
    ):
        raise ActionContractError(
            "Action has no valid reviewed Tier 0 adapter."
        )

    return specification.execute()
