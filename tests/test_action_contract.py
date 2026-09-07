#!/usr/bin/env python3

import unittest
from dataclasses import FrozenInstanceError, replace
from unittest.mock import patch

import action_contract


SESSION_ID = "a" * 32
OTHER_SESSION_ID = "b" * 32


class ActionContractTests(unittest.TestCase):
    def create_request(
        self,
        interface=action_contract.DESKTOP_CLI,
    ) -> action_contract.ActionRequest:
        with patch.object(
            action_contract.session_context,
            "get_session_id",
            return_value=SESSION_ID,
        ):
            return action_contract.create_action_request(
                "tasks.read",
                interface=interface,
            )

    def create_grocery_request(
        self,
        item: str = "Milk",
    ) -> action_contract.ActionRequest:
        with patch.object(
            action_contract.session_context,
            "get_session_id",
            return_value=SESSION_ID,
        ):
            return action_contract.create_action_request(
                "groceries.add",
                interface=action_contract.DESKTOP_CLI,
                arguments={"item": item},
            )

    def assert_contract_error(
        self,
        request: action_contract.ActionRequest,
    ) -> None:
        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaises(
                action_contract.ActionContractError,
            ),
        ):
            action_contract.validate_action_request(request)

    def test_factory_creates_immutable_slotted_contract(
        self,
    ) -> None:
        request = self.create_request()

        self.assertEqual(request.action, "tasks.read")
        self.assertEqual(request.record_type, "task")
        self.assertEqual(request.target, "tasks")
        self.assertEqual(request.arguments, ())
        self.assertEqual(request.risk_tier, action_contract.TIER_0)
        self.assertEqual(request.session_id, SESSION_ID)
        self.assertEqual(
            request.interface,
            action_contract.DESKTOP_CLI,
        )
        self.assertFalse(hasattr(request, "__dict__"))

        with self.assertRaises(FrozenInstanceError):
            request.action = "different.action"

        with self.assertRaises(AttributeError):
            request.arguments.append(("filter", "open"))

    def test_factory_normalizes_empty_tasks_read_arguments(
        self,
    ) -> None:
        with patch.object(
            action_contract.session_context,
            "get_session_id",
            return_value=SESSION_ID,
        ):
            request = action_contract.create_action_request(
                "tasks.read",
                interface=action_contract.DESKTOP_CLI,
                arguments={},
            )

        self.assertEqual(request.target, "tasks")
        self.assertEqual(request.arguments, ())

    def test_factory_rejects_malformed_tasks_read_arguments(
        self,
    ) -> None:
        malformed_arguments = (
            False,
            0,
            "",
            [],
            (),
            {"filter": "open"},
        )

        for arguments in malformed_arguments:
            with (
                self.subTest(arguments=arguments),
                self.assertRaises(
                    action_contract.ActionContractError,
                ),
            ):
                action_contract.create_action_request(
                    "tasks.read",
                    interface=action_contract.DESKTOP_CLI,
                    arguments=arguments,
                )

    def test_factory_represents_tier_one_grocery_add(self) -> None:
        request = self.create_grocery_request("  Whole milk  ")

        self.assertEqual(request.action, "groceries.add")
        self.assertEqual(request.record_type, "grocery")
        self.assertEqual(request.target, "grocery_list")
        self.assertEqual(request.arguments, (("item", "Whole milk"),))
        self.assertEqual(request.risk_tier, action_contract.TIER_1)
        self.assertIs(
            action_contract._ACTION_REGISTRY["groceries.add"].execute,
            None,
        )

    def test_grocery_add_does_not_truncate_item(self) -> None:
        item = "x" * 10_000

        request = self.create_grocery_request(item)

        self.assertEqual(request.arguments, (("item", item),))

    def test_factory_rejects_malformed_grocery_arguments(self) -> None:
        class DictSubclass(dict):
            pass

        class StringSubclass(str):
            pass

        malformed_arguments = (
            None, False, 0, "Milk", [], (), {},
            {"other": "Milk"},
            {"item": "Milk", "other": "Eggs"},
            {1: "Milk"},
            {StringSubclass("item"): "Milk"},
            DictSubclass(item="Milk"),
            {"item": StringSubclass("Milk")},
            {"item": None},
            {"item": False},
            {"item": ""},
            {"item": "   "},
            {"item": "Milk\nEggs"},
            {"item": "Milk\rEggs"},
            {"item": "Milk\vEggs"},
            {"item": "Milk\fEggs"},
            {"item": "Milk\x1cEggs"},
            {"item": "Milk\x1dEggs"},
            {"item": "Milk\x1eEggs"},
            {"item": "Milk\x85Eggs"},
            {"item": "Milk\u2028Eggs"},
            {"item": "Milk\u2029Eggs"},
            {"item": "\u2028Milk"},
            {"item": "Milk\u2029"},
        )

        for arguments in malformed_arguments:
            with (
                self.subTest(arguments=arguments),
                self.assertRaises(action_contract.ActionContractError),
            ):
                action_contract.create_action_request(
                    "groceries.add",
                    interface=action_contract.DESKTOP_CLI,
                    arguments=arguments,
                )

    def test_validator_rejects_noncanonical_grocery_arguments(self) -> None:
        request = self.create_grocery_request()
        malformed_arguments = (
            (("item", " Milk "),),
            (("item", "Milk"), ("item", "Eggs")),
            (("other", "Milk"),),
            (["item", "Milk"],),
        )

        for arguments in malformed_arguments:
            with self.subTest(arguments=arguments):
                self.assert_contract_error(
                    replace(request, arguments=arguments)
                )

    def test_executor_refuses_valid_grocery_add_without_mutation(self) -> None:
        request = self.create_grocery_request()

        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            patch.object(action_contract.read_tasks, "handle") as handle,
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "Only Tier 0 actions may execute",
            ),
        ):
            action_contract._execute_reviewed_tier_zero_action(request)

        handle.assert_not_called()

    def test_registry_metadata_is_immutable(self) -> None:
        specification = action_contract._ACTION_REGISTRY["tasks.read"]

        with self.assertRaises(TypeError):
            action_contract._ACTION_REGISTRY["tasks.read"] = specification

        with self.assertRaises(FrozenInstanceError):
            specification.risk_tier = action_contract.TIER_1

    def test_registry_rejects_unknown_risk_tier(self) -> None:
        malformed = replace(
            action_contract._ACTION_REGISTRY["tasks.read"],
            risk_tier=2,
        )

        with (
            patch.object(
                action_contract,
                "_ACTION_REGISTRY",
                {"tasks.read": malformed},
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "Invalid action specification",
            ),
        ):
            self.create_request()

    def test_registry_rejects_tier_one_execution_adapter(self) -> None:
        mutation_capable_call = unittest.mock.Mock()
        malformed = replace(
            action_contract._ACTION_REGISTRY["groceries.add"],
            execute=mutation_capable_call,
        )

        with (
            patch.object(
                action_contract,
                "_ACTION_REGISTRY",
                {"groceries.add": malformed},
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "must not have an execution adapter",
            ),
        ):
            self.create_grocery_request()

        mutation_capable_call.assert_not_called()

    def test_registry_rejects_unreviewed_argument_normalizer(self) -> None:
        request = self.create_request()
        unreviewed_normalizer = unittest.mock.Mock(return_value=())
        malformed = replace(
            action_contract._ACTION_REGISTRY["tasks.read"],
            normalize_arguments=unreviewed_normalizer,
        )

        with (
            patch.object(
                action_contract,
                "_ACTION_REGISTRY",
                {"tasks.read": malformed},
            ),
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "Invalid action argument normalizer",
            ),
        ):
            action_contract._execute_reviewed_tier_zero_action(request)

        unreviewed_normalizer.assert_not_called()

    def test_executor_rejects_unreviewed_tier_zero_adapter(self) -> None:
        request = self.create_request()
        unreviewed_adapter = unittest.mock.Mock(return_value="unsafe")
        malformed = replace(
            action_contract._ACTION_REGISTRY["tasks.read"],
            execute=unreviewed_adapter,
        )

        with (
            patch.object(
                action_contract,
                "_ACTION_REGISTRY",
                {"tasks.read": malformed},
            ),
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "Invalid Tier 0 execution adapter",
            ),
        ):
            action_contract._execute_reviewed_tier_zero_action(request)

        unreviewed_adapter.assert_not_called()

    def test_registry_rejects_malformed_specification_object(self) -> None:
        request = self.create_request()

        with (
            patch.object(
                action_contract,
                "_ACTION_REGISTRY",
                {"tasks.read": object()},
            ),
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "Invalid action specification",
            ),
        ):
            action_contract._execute_reviewed_tier_zero_action(request)

    def test_factory_rejects_unknown_action(self) -> None:
        with self.assertRaisesRegex(
            action_contract.ActionContractError,
            "Unknown action",
        ):
            action_contract.create_action_request(
                "tasks.delete",
                interface=action_contract.DESKTOP_CLI,
            )

    def test_factory_rejects_malformed_action_before_lookup(
        self,
    ) -> None:
        for action in (None, False, 1, [], {}):
            with (
                self.subTest(action=action),
                self.assertRaises(
                    action_contract.ActionContractError,
                ),
            ):
                action_contract.create_action_request(
                    action,
                    interface=action_contract.DESKTOP_CLI,
                )

    def test_factory_rejects_malformed_interface_before_lookup(
        self,
    ) -> None:
        for interface in (None, False, 1, [], {}):
            with (
                self.subTest(interface=interface),
                self.assertRaises(
                    action_contract.ActionContractError,
                ),
            ):
                action_contract.create_action_request(
                    "tasks.read",
                    interface=interface,
                )

    def test_validator_rejects_unknown_action(self) -> None:
        request = replace(
            self.create_request(),
            action="tasks.delete",
        )

        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "Unknown action",
            ),
        ):
            action_contract.validate_action_request(request)

    def test_validator_rejects_malformed_action_before_lookup(
        self,
    ) -> None:
        for action in (None, False, 1, [], {}):
            with self.subTest(action=action):
                self.assert_contract_error(
                    replace(
                        self.create_request(),
                        action=action,
                    )
                )

    def test_validator_rejects_record_type_tampering(
        self,
    ) -> None:
        request = replace(
            self.create_request(),
            record_type="note",
        )

        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "record type",
            ),
        ):
            action_contract.validate_action_request(request)

    def test_validator_rejects_target_tampering(self) -> None:
        request = replace(
            self.create_request(),
            target="notes",
        )

        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "target",
            ),
        ):
            action_contract.validate_action_request(request)

    def test_validator_rejects_malformed_target(self) -> None:
        for target in (None, False, 1, [], {}):
            with self.subTest(target=target):
                self.assert_contract_error(
                    replace(
                        self.create_request(),
                        target=target,
                    )
                )

    def test_validator_rejects_argument_tampering(self) -> None:
        malformed_arguments = (
            (("filter", "open"),),
            [],
            {},
            None,
            "",
        )

        for arguments in malformed_arguments:
            with self.subTest(arguments=arguments):
                self.assert_contract_error(
                    replace(
                        self.create_request(),
                        arguments=arguments,
                    )
                )

    def test_validator_rejects_malformed_record_type(
        self,
    ) -> None:
        for record_type in (None, False, 1, [], {}):
            with self.subTest(record_type=record_type):
                self.assert_contract_error(
                    replace(
                        self.create_request(),
                        record_type=record_type,
                    )
                )

    def test_validator_rejects_risk_tier_tampering(
        self,
    ) -> None:
        for risk_tier in (1, False, 0.0, "0", None):
            with self.subTest(risk_tier=risk_tier):
                self.assert_contract_error(
                    replace(
                        self.create_request(),
                        risk_tier=risk_tier,
                    )
                )

    def test_factory_rejects_invalid_current_session(self) -> None:
        for session_id in (None, "short", False, 1, [], {}):
            with (
                self.subTest(session_id=session_id),
                patch.object(
                    action_contract.session_context,
                    "get_session_id",
                    return_value=session_id,
                ),
                self.assertRaises(
                    action_contract.ActionContractError,
                ),
            ):
                action_contract.create_action_request(
                    "tasks.read",
                    interface=action_contract.DESKTOP_CLI,
                )

    def test_validator_rejects_malformed_request_session(
        self,
    ) -> None:
        for session_id in (None, False, 1, [], {}):
            with self.subTest(session_id=session_id):
                self.assert_contract_error(
                    replace(
                        self.create_request(),
                        session_id=session_id,
                    )
                )

    def test_validator_rejects_mismatched_session(self) -> None:
        request = self.create_request()

        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=OTHER_SESSION_ID,
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "does not match",
            ),
        ):
            action_contract.validate_action_request(request)

    def test_factory_rejects_invalid_interface(self) -> None:
        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaisesRegex(
                action_contract.ActionContractError,
                "interface",
            ),
        ):
            action_contract.create_action_request(
                "tasks.read",
                interface="web",
            )

    def test_browser_is_structurally_valid(self) -> None:
        request = self.create_request(interface=action_contract.BROWSER)

        self.assertEqual(request.interface, action_contract.BROWSER)

        with patch.object(
            action_contract.session_context,
            "get_session_id",
            return_value=SESSION_ID,
        ):
            self.assertIs(
                action_contract.validate_action_request(request),
                request,
            )

    def test_validator_rejects_malformed_interface(
        self,
    ) -> None:
        for interface in (None, False, 1, [], {}):
            with self.subTest(interface=interface):
                self.assert_contract_error(
                    replace(
                        self.create_request(),
                        interface=interface,
                    )
                )

    def test_executor_runs_registered_tier_zero_adapter(
        self,
    ) -> None:
        request = self.create_request()

        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            patch.object(
                action_contract.read_tasks,
                "handle",
                return_value="EXACT TASK OUTPUT",
            ) as handle,
        ):
            response = action_contract._execute_reviewed_tier_zero_action(request)

        self.assertEqual(response, "EXACT TASK OUTPUT")
        handle.assert_called_once_with("")

    def test_executor_fails_closed_for_non_tier_zero(
        self,
    ) -> None:
        request = replace(
            self.create_request(),
            risk_tier=1,
        )

        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            patch.object(
                action_contract.read_tasks,
                "handle",
            ) as handle,
            self.assertRaises(
                action_contract.ActionContractError,
            ),
        ):
            action_contract._execute_reviewed_tier_zero_action(request)

        handle.assert_not_called()

    def test_request_hash_is_stable_for_same_request(self) -> None:
        request = self.create_request()

        self.assertEqual(
            action_contract.request_hash(request),
            action_contract.request_hash(request),
        )


    def test_request_hash_binds_browser_interface(self) -> None:
        desktop = self.create_request()
        browser = self.create_request(interface=action_contract.BROWSER)

        self.assertNotEqual(
            action_contract.request_hash(desktop),
            action_contract.request_hash(browser),
        )

    def test_request_hash_changes_when_operation_changes(self) -> None:
        first = self.create_grocery_request("Milk")
        second = self.create_grocery_request("Eggs")

        self.assertNotEqual(
            action_contract.request_hash(first),
            action_contract.request_hash(second),
        )


    def test_request_hash_does_not_include_session_identity(self) -> None:
        request = self.create_request()

        changed_session = replace(
            request,
            session_id=OTHER_SESSION_ID,
        )

        self.assertEqual(
            action_contract.request_hash(request),
            action_contract.request_hash(changed_session),
        )

    def test_request_hash_rejects_tampered_request(self) -> None:
        request = self.create_request()

        tampered = replace(
            request,
            target="different-target",
        )

        with (
            patch.object(
                action_contract.session_context,
                "get_session_id",
                return_value=SESSION_ID,
            ),
            self.assertRaises(action_contract.ActionContractError),
        ):
            action_contract.request_hash(tampered)


if __name__ == "__main__":
    unittest.main()
