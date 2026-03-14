import unittest
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


class FrontendInteractionTest(unittest.TestCase):
    def test_app_contains_interaction_hooks(self):
        script = (FRONTEND_DIR / "app.js").read_text(encoding="utf-8")

        for marker in [
            "function autoResizeChatInput()",
            "function syncChartStageAccent(",
            "elements.chatInput.addEventListener('input'",
        ]:
            self.assertIn(marker, script)

    def test_styles_contain_motion_classes(self):
        css = (FRONTEND_DIR / "styles.css").read_text(encoding="utf-8")

        for marker in [
            ".message--enter",
            "@keyframes message-in",
            ".chart-container--main[data-view=\"industry\"]",
        ]:
            self.assertIn(marker, css)


if __name__ == "__main__":
    unittest.main()
