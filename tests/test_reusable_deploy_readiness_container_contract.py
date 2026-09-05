import os
import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "reusable-codestra-deploy-readiness.yml"


def resolver_source() -> str:
    text = WORKFLOW.read_text(encoding="utf-8")
    start = text.index("          import os\n", text.index("readarray -t container_paths"))
    end = text.index("          PY\n", start)
    return textwrap.dedent(text[start:end])


def resolve(tmp_path: Path, dockerfile: str = "", context: str = ""):
    env = os.environ | {
        "CONFIGURED_DOCKERFILE": dockerfile,
        "CONFIGURED_BUILD_CONTEXT": context,
    }
    return subprocess.run(
        ["python", "-c", resolver_source()], cwd=tmp_path, env=env,
        check=False, capture_output=True, text=True,
    )


def test_explicit_root_context_supports_nested_dockerfile(tmp_path):
    dockerfile = tmp_path / "vicidial" / "docker" / "Dockerfile"
    dockerfile.parent.mkdir(parents=True)
    dockerfile.write_text("FROM scratch\n", encoding="utf-8")

    result = resolve(tmp_path, "vicidial/docker/Dockerfile", ".")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["vicidial/docker/Dockerfile", "."]


def test_default_layout_keeps_dockerfile_directory_context(tmp_path):
    dockerfile = tmp_path / "service" / "Dockerfile"
    dockerfile.parent.mkdir()
    dockerfile.write_text("FROM scratch\n", encoding="utf-8")

    result = resolve(tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["service/Dockerfile", "service"]


def test_container_paths_reject_traversal(tmp_path):
    result = resolve(tmp_path, "../Dockerfile", ".")

    assert result.returncode != 0
    assert "must be repository-relative" in result.stderr


def test_release_passes_verified_metadata_as_build_arguments():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '--build-arg "SOURCE_SHA=${source_sha}"' in text
    assert '--build-arg "BUILD_DATE=${build_date}"' in text
    assert 'source_sha="$(git rev-parse HEAD)"' in text
    assert 'build_date="$(git show -s --format=%cI "$source_sha")"' in text
