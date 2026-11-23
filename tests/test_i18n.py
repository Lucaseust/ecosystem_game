"""Translation must preserve rules, identities, free text and launcher settings."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from eco import campaign, debrief, desktop, i18n


class TranslationTests(unittest.TestCase):
    def test_view_translation_does_not_change_state_protocol_or_player_content(self):
        game = campaign.Game(campaign.new_state(code="TEST", seed="translation"))
        token = game.join(code="TEST", first_name="Nom", last_name="Territoire")
        game.step()
        team = game.state["players"][token]["team"]
        role = game.state["players"][token]["role"]
        game.state["teams"][team]["claims"][role] = {"text": "Votre entreprise, crédits, Nom"}
        game.c(team)["discussion"] = [{"text": "Votre entreprise, crédits, Nom"}]
        game.c(team)["positions"] = {role: {"text": "Votre entreprise, crédits, Nom"}}
        original = game.player_view(token)
        state = copy.deepcopy(game.state)
        translated = i18n.view(original, "en")
        self.assertEqual(translated["phase"], "JANUARY")
        self.assertIn("January", translated["phase_label"])
        self.assertEqual(translated["me"]["name"], "Nom Territoire")
        self.assertEqual(translated["team"]["claims"], original["team"]["claims"])
        self.assertEqual(translated["team"]["discussion"], original["team"]["discussion"])
        self.assertEqual(translated["team"]["positions"], original["team"]["positions"])
        self.assertEqual(translated["me"]["cash"], 2000)
        self.assertEqual(game.state, state)
        self.assertEqual(i18n.view(original, "fr"), original)

    def test_catalogue_is_valid_and_has_no_empty_entries(self):
        self.assertGreater(len(i18n.catalog()), 500)
        self.assertTrue(all(k.strip() and v.strip() for k, v in i18n.catalog().items()))
        self.assertEqual(i18n.translate("Votre entreprise", "en"), "Your company")

    def test_english_offline_report_embeds_localisation_without_server_calls(self):
        root = Path(__file__).resolve().parents[1]
        game = campaign.Game(campaign.new_state(code="TEST"))
        while game.state["phase"] != "FINAL":
            game.step()
        script = (root / "web" / "debrief.js").read_text(encoding="utf-8")
        report = debrief.html_report(debrief.build(game), "body{}", script, "TEST", language="en")
        self.assertIn('<html lang="en">', report)
        self.assertIn("Session report TEST", report)
        self.assertIn("EcoI18n.configure", report)
        self.assertNotIn("<script src=", report)
        self.assertNotIn(game.state["host_key"], report)

    def test_launcher_language_preserves_canonical_settings_and_private_key(self):
        import tkinter as tk

        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(str(exc))
        root.withdraw()
        previous = desktop.LANGUAGE
        try:
            with tempfile.TemporaryDirectory() as folder:
                settings = desktop.Settings(language="en", mode=desktop.MODES[2], key="Nom")
                app = desktop.DesktopApp(root, Path(folder) / "prefs.json", settings=settings)
                self.assertEqual(app.current_settings(), settings)
                self.assertEqual(app.start_button.cget("text"), "Start the server")
                self.assertIn("--lang", settings.command("Nom"))
                self.assertEqual(app.vars["language"].get(), "English")
                opened = []
                app.open_file = opened.append
                app.open_readme()
                self.assertEqual(opened[-1].name, "NOTICE.html")
                self.assertTrue(opened[-1].is_file())
                app.vars["language"].set("Français")
                app.change_language()
                self.assertEqual(desktop.LANGUAGE, "fr")
                app.open_readme()
                self.assertEqual(opened[-1].name, "NOTICE.fr.html")
                self.assertTrue(opened[-1].is_file())
        finally:
            root.destroy()
            desktop.LANGUAGE = previous


if __name__ == "__main__":
    unittest.main()
