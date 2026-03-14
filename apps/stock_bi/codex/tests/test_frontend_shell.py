import unittest
from pathlib import Path


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


class FrontendShellTest(unittest.TestCase):
    def test_editorial_shell_markers_exist(self):
        html = (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")

        for marker in [
            'id="marketPulse"',
            'id="signalStrip"',
            'id="heroBrief"',
            'id="commandDeck"',
            'id="assistantConsole"',
        ]:
            self.assertIn(marker, html)


if __name__ == "__main__":
    unittest.main()
