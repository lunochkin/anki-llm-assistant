"""
CLI parser builder for Anki LLM Assistant.

This module handles loading the CLI specification from YAML and building
the argparse parser from that specification.
"""

import yaml
import argparse
from pathlib import Path


def load_cli_spec():
    """Load CLI specification from specs/cli.yaml"""
    spec_path = Path(__file__).parent.parent.parent / "specs" / "cli.yaml"
    with open(spec_path, "r") as f:
        return yaml.safe_load(f)


def build_parser_from_spec(spec):
    """Build argparse parser from CLI specification"""
    parser = argparse.ArgumentParser(
        description=spec["description"]
    )
    
    # Add global options from spec
    for option in spec["global_options"]:
        option_name = option["name"]
        option_args = {}
        
        # Handle different option types
        if option["type"] == "boolean":
            option_args["action"] = "store_true"
        elif option["type"] == "string":
            if "choices" in option:
                option_args["choices"] = option["choices"]
            if "default" in option:
                option_args["default"] = option["default"]
        elif option["type"] == "float":
            option_args["type"] = float
            if "default" in option:
                option_args["default"] = option["default"]
        
        # Add help text if available
        if "description" in option:
            option_args["help"] = option["description"]
        
        parser.add_argument(option_name, **option_args)
    
    # Add subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add public commands
    for cmd_name, cmd_spec in spec["commands"]["public"].items():
        subparser = subparsers.add_parser(cmd_name, help=cmd_spec["description"])
        # Add command-specific arguments if any
        for arg in cmd_spec.get("arguments", []):
            arg_args = {}
            
            # Handle different argument types
            if arg["type"] == "float":
                arg_args["type"] = float
                if "default" in arg:
                    arg_args["default"] = arg["default"]
            elif arg["type"] == "string":
                if "default" in arg:
                    arg_args["default"] = arg["default"]
            
            # Add help text if available
            if "description" in arg:
                arg_args["help"] = arg["description"]
            
            subparser.add_argument(arg["name"], **arg_args)
    
    # Add dev/test commands
    for cmd_name, cmd_spec in spec["commands"]["dev_test"].items():
        subparser = subparsers.add_parser(cmd_name, help=cmd_spec["description"])
        # Add command-specific arguments if any
        for arg in cmd_spec.get("arguments", []):
            arg_args = {}
            
            # Handle different argument types
            if arg["type"] == "float":
                arg_args["type"] = float
                if "default" in arg:
                    arg_args["default"] = arg["default"]
            elif arg["type"] == "string":
                if "default" in arg:
                    arg_args["default"] = arg["default"]
            
            # Add help text if available
            if "description" in arg:
                arg_args["help"] = arg["description"]
            
            subparser.add_argument(arg["name"], **arg_args)
    
    return parser
