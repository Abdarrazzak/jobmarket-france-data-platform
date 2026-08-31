from pathlib import Path


def test_required_directories_exist() -> None:
    required_directories = [
        "dags",
        "src/jobmarket",
        "api",
        "dashboard",
        "configs",
        "docs",
        "tests",
    ]

    for directory in required_directories:
        assert Path(directory).is_dir(), f"Missing directory: {directory}"


def test_required_documentation_exists() -> None:
    required_files = [
        "README.md",
        "docs/ARCHITECTURE.md",
        "docs/DATA_MODEL.md",
        "docs/API.md",
        "docs/DEPLOYMENT.md",
        "docs/ROADMAP.md",
    ]

    for file_path in required_files:
        assert Path(file_path).is_file(), f"Missing file: {file_path}"

