import json
import sys


def main() -> None:
    sys.stdin.read()
    message = (
        "Project workflow: Requirements -> Architecture -> Design Review -> "
        "Implementation Planning -> Implementation -> Code Review -> "
        "Verification -> Pull Request. Use the SDLC Orchestrator Agent and "
        "matching role skills. Pause for required human approvals; do not "
        "invent missing information or claim unrun checks passed."
    )
    print(json.dumps({"systemMessage": message}))


if __name__ == "__main__":
    main()