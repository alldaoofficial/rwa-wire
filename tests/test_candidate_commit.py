"""Exercise the real CI commit block with concurrent disposable build changes."""
import pathlib
import subprocess
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class CandidateCommitTest(unittest.TestCase):
    def test_story_commit_rebases_without_generated_artifacts(self):
        workflow = (ROOT / ".github/workflows/candidate-generator.yml").read_text()
        block = workflow.split("      - name: Commit generated story package", 1)[1]
        block = block.split("      - name: Deploy generated article", 1)[0]
        script = textwrap.dedent(block.split("        run: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            def git(folder, *args):
                return subprocess.check_output(["git", "-C", str(folder), *args], stderr=subprocess.STDOUT).decode()
            remote = base / "remote.git"
            subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(remote)], check=True, capture_output=True)
            job = base / "job"
            subprocess.run(["git", "clone", str(remote), str(job)], check=True, capture_output=True)
            git(job, "config", "user.name", "Fixture")
            git(job, "config", "user.email", "fixture@example.invalid")
            def write(folder, name, value):
                path = folder / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(value)
            for name in ["src/content/articles/base.mdx", "public/images/news/base.svg", "publish/candidates/base.json", "dist/index.html", ".astro/content.d.ts", "node_modules/package/index.js", "scripts/__pycache__/cache.pyc", "public/sitemap.xml"]:
                write(job, name, "baseline")
            git(job, "add", "."); git(job, "commit", "-m", "baseline"); git(job, "push", "origin", "main")
            other = base / "other"
            subprocess.run(["git", "clone", str(remote), str(other)], check=True, capture_output=True)
            git(other, "config", "user.name", "Fixture"); git(other, "config", "user.email", "fixture@example.invalid")
            write(other, "dist/index.html", "concurrent build")
            write(other, "dist/de/index.html", "concurrent localized build")
            git(other, "add", "dist"); git(other, "commit", "-m", "concurrent build"); git(other, "push")
            for name in ["dist/index.html", "dist/de/index.html", ".astro/content.d.ts", "node_modules/package/index.js", "scripts/__pycache__/cache.pyc", "public/sitemap.xml"]:
                write(job, name, "local disposable build")
            expected = ["src/content/articles/story.mdx", "public/images/news/story.svg", "publish/candidates/story.json"]
            for name in expected: write(job, name, "story package")
            subprocess.run(["bash", "-eu", "-c", script], cwd=job, check=True, capture_output=True)
            changed = git(job, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
            self.assertEqual(sorted(expected), sorted(changed))
            self.assertEqual((job / "dist/index.html").read_text(), "concurrent build")
            self.assertEqual((job / "dist/de/index.html").read_text(), "concurrent localized build")
            self.assertEqual(git(job, "status", "--porcelain"), "")


if __name__ == "__main__": unittest.main()
