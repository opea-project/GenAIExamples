# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import sys
from types import SimpleNamespace

import click
from core.config import EXAMPLE_CONFIGS
from core.deployer import Deployer
from core.utils import log_message, setup_logging, stop_all_kubectl_port_forwards


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose (DEBUG) logging.")
def cli(verbose):
    """An interactive one-click deployment script for GenAIExamples."""
    setup_logging()
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        log_message("DEBUG", "Verbose mode enabled.")

    app_args = SimpleNamespace(verbose=verbose)

    try:
        # 1. Choose an example
        example_names = list(EXAMPLE_CONFIGS.keys())

        example_prompt_lines = ["Please choose an example to manage:"]
        for i, name in enumerate(example_names, 1):
            example_prompt_lines.append(f"  [{i}] {name}")
        example_prompt_text = "\n".join(example_prompt_lines)

        example_choice_num = click.prompt(
            example_prompt_text, type=click.IntRange(1, len(example_names)), default=1, show_default=True
        )

        example_name = example_names[example_choice_num - 1]
        log_message("INFO", f"Example selected: '{example_name}'")
        app_args.example = example_name

        deployment_types = ["Online Deployment", "Offline Deployment Management"]
        deployment_type_prompt_lines = ["Please choose the deployment type:"]
        for i, name in enumerate(deployment_types, 1):
            deployment_type_prompt_lines.append(f"  [{i}] {name}")
        deployment_type_prompt_text = "\n".join(deployment_type_prompt_lines)
        deployment_type_choice_num = click.prompt(
            deployment_type_prompt_text, type=click.IntRange(1, len(deployment_types)), default=1, show_default=True
        )
        deployment_type_choice = deployment_types[deployment_type_choice_num - 1]

        log_message("INFO", f"Deployment type selected: '{deployment_type_choice}'")

        if deployment_type_choice == "Offline Deployment Management":
            # Check config to see if offline mode is supported for the selected example
            supported_offline_modes = EXAMPLE_CONFIGS[example_name].get("offline_support", [])
            if not supported_offline_modes:
                log_message("ERROR", f"Offline mode is not currently supported for the '{example_name}' example.")
                sys.exit(1)
            # Pass the supported modes to the deployer for later use
            app_args.supported_offline_modes = supported_offline_modes

        deployer = Deployer(app_args)

        if deployment_type_choice == "Online Deployment":
            # 2. Choose an action (original flow)
            actions = ["Deploy", "Clear", "Test Connection"]
            action_prompt_lines = ["Please choose an action:"]
            for i, desc in enumerate(actions, 1):
                action_prompt_lines.append(f"  [{i}] {desc}")
            action_prompt_text = "\n".join(action_prompt_lines)
            action_choice_num = click.prompt(
                action_prompt_text, type=click.IntRange(1, len(actions)), default=1, show_default=True
            )
            action = actions[action_choice_num - 1]
            log_message("INFO", f"Action selected: '{action}'")
            app_args.action = action

            # 3. Execute
            if action == "Deploy":
                deployer.run_interactive_deployment()
            elif action == "Clear":
                deployer.run_interactive_clear()
            elif action == "Test Connection":
                deployer.run_interactive_test()

        elif deployment_type_choice == "Offline Deployment Management":
            # New flow for offline management
            deployer.manage_offline_deployment()

    except (ValueError, click.exceptions.Abort) as e:
        log_message("WARN", f"Operation aborted by user or invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        log_message("ERROR", f"An unhandled error occurred: {e}")
        logging.error(e, exc_info=True)
        sys.exit(1)
    finally:
        stop_all_kubectl_port_forwards()
        log_message("INFO", "Script finished.")


if __name__ == "__main__":
    cli()
