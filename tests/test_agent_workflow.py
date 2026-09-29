import json
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CUSTOMIZATION_ROOT = PROJECT_ROOT / ".github"
EXPECTED_SKILLS = {
    "architecture",
    "code-review",
    "design-review",
    "implementation",
    "implementation-planning",
    "orchestration",
    "pull-request",
    "requirements",
    "verification",
}


def test_each_agent_references_a_discoverable_role_skill():
    agent_files = list((CUSTOMIZATION_ROOT / "agents").glob("*.agent.md"))
    skill_directories = {
        path.name: path
        for path in (CUSTOMIZATION_ROOT / "skills").iterdir()
        if path.is_dir()
    }

    assert len(agent_files) == len(EXPECTED_SKILLS)
    assert set(skill_directories) == EXPECTED_SKILLS

    referenced_skills = set()
    for agent_file in agent_files:
        content = agent_file.read_text(encoding="utf-8")
        frontmatter = content.split("---", 2)[1]
        assert re.search(r"^description:\s*.+$", frontmatter, re.MULTILINE)

        skill_reference = re.search(r"(?:Use|using) the `([a-z0-9-]+)` skill", content)
        assert skill_reference is not None, agent_file
        skill_name = skill_reference.group(1)
        referenced_skills.add(skill_name)
        skill_file = skill_directories[skill_name] / "SKILL.md"
        assert skill_file.is_file(), skill_file

        skill_frontmatter = skill_file.read_text(encoding="utf-8").split("---", 2)[1]
        assert re.search(rf"^name:\s*{re.escape(skill_name)}\s*$", skill_frontmatter, re.MULTILINE)

    assert referenced_skills == EXPECTED_SKILLS
    assert not list((CUSTOMIZATION_ROOT / "prompts").glob("*.prompt.md"))


def test_authoritative_sdlc_artifacts_exist_at_repository_root():
    expected_artifacts = (
        "requirements.md",
        "architecture.md",
        "design-review.md",
        "impl-plan.md",
    )

    for artifact in expected_artifacts:
        artifact_path = PROJECT_ROOT / artifact
        assert artifact_path.is_file(), artifact_path
        assert artifact_path.stat().st_size > 0, artifact_path


def test_session_start_hook_emits_workflow_context():
    hook_config_path = CUSTOMIZATION_ROOT / "hooks" / "workflow-hooks.json"
    hook_config = json.loads(hook_config_path.read_text(encoding="utf-8"))
    hook = hook_config["hooks"]["SessionStart"][0]
    assert hook["command"].endswith("workflow_context.py")

    hook_script = CUSTOMIZATION_ROOT / "hooks" / "workflow_context.py"
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input="{}",
        text=True,
        capture_output=True,
        check=True,
        cwd=PROJECT_ROOT,
    )

    response = json.loads(result.stdout)
    assert "systemMessage" in response
    assert "Requirements -> Architecture" in response["systemMessage"]