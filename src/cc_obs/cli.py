import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="cc-obs",
        description="Observability for Claude Code sessions",
    )
    sub = parser.add_subparsers(dest="command")

    # install
    p_install = sub.add_parser("install", help="Install observer hooks")
    p_install.add_argument(
        "--project",
        action="store_true",
        help="Write to settings.json instead of settings.local.json",
    )
    p_install.add_argument(
        "--uninstall", action="store_true", help="Remove all cc-obs hooks"
    )
    p_install.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="Install to ~/.claude/settings.json",
    )
    p_install.add_argument(
        "--no-prompt",
        action="store_true",
        help="Run non-interactively with default settings",
    )

    # log
    sub.add_parser("log", help="Observer hook handler (reads stdin)")

    # wrap
    p_wrap = sub.add_parser("wrap", help="Wrap a hook command with timing")
    p_wrap.add_argument("--name", default="", help="Display label for the wrapped hook")
    p_wrap.add_argument(
        "cmd", nargs=argparse.REMAINDER, help="Command to wrap (after --)"
    )

    # view
    p_view = sub.add_parser("view", help="Generate and open HTML viewer")
    p_view.add_argument(
        "--no-open", action="store_true", help="Generate without opening browser"
    )
    p_view.add_argument("--log-file", help="Read events from a specific JSONL file")

    # clear
    p_clear = sub.add_parser("clear", help="Delete log and view files")
    p_clear.add_argument("--quiet", action="store_true", help="Suppress output")

    # status
    sub.add_parser("status", help="Print session summary")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    match args.command:
        case "install":
            from cc_obs.commands.install import run

            run(
                project=args.project,
                global_install=args.global_install,
                uninstall=args.uninstall,
                no_prompt=args.no_prompt,
            )
        case "log":
            from cc_obs.commands.log import run

            run()
        case "wrap":
            from cc_obs.commands.wrap import run

            cmd = args.cmd
            if cmd and cmd[0] == "--":
                cmd = cmd[1:]
            run(cmd, name=args.name)
        case "view":
            from cc_obs.commands.view import run

            run(no_open=args.no_open, log_file=args.log_file)
        case "clear":
            from cc_obs.commands.clear import run

            run(quiet=args.quiet)
        case "status":
            from cc_obs.commands.status import run

            run()
