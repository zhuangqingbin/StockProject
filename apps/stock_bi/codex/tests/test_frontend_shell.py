import unittest
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
BACKEND_MAIN = Path(__file__).resolve().parents[1] / "backend" / "main.py"


class FrontendShellTest(unittest.TestCase):
    def test_react_frontend_toolchain_exists(self):
        for relative_path in [
            "package.json",
            "tsconfig.json",
            "vite.config.ts",
            "src/main.tsx",
            "src/App.tsx",
            "src/styles/app.css",
        ]:
            self.assertTrue((FRONTEND_DIR / relative_path).exists(), relative_path)

    def test_backend_serves_built_frontend_assets(self):
        content = BACKEND_MAIN.read_text(encoding="utf-8")

        self.assertIn('os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")', content)
        self.assertIn('app.mount("/assets"', content)
        self.assertIn('FileResponse(index_path)', content)


if __name__ == "__main__":
    unittest.main()
