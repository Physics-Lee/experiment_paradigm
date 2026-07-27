import ast
import os
import unittest
from pathlib import Path


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from experiment_paradigm import (
    BaseParadigm,
    ListeningParadigm,
    LockedInSentenceReadingParadigm,
    ReadingParadigm,
    RelaxingNewsParadigm,
    SentenceParadigm,
)
from experiment_paradigm.cli import (
    main_relaxing_news as compatibility_news_main,
    parse_locked_in_args as compatibility_locked_parser,
)
from experiment_paradigm.commands.locked_in_reading import (
    parse_locked_in_args,
)
from experiment_paradigm.commands.relaxing_news import (
    main_relaxing_news,
    parse_relaxing_news_args,
)
from experiment_paradigm.core import validate_duration_range
from experiment_paradigm.paradigms.listening import (
    ListeningParadigm as SplitListeningParadigm,
)
from experiment_paradigm.paradigms.locked_in_reading import (
    LockedInSentenceReadingParadigm as SplitLockedInParadigm,
)
from experiment_paradigm.paradigms.reading import (
    ReadingParadigm as SplitReadingParadigm,
)
from experiment_paradigm.paradigms.relaxing_news import (
    RelaxingNewsParadigm as SplitNewsParadigm,
)
from experiment_paradigm.paradigms.sentence import (
    SentenceParadigm as SplitSentenceParadigm,
)


class RepositoryStructureTests(unittest.TestCase):
    def test_public_paradigm_imports_resolve_to_split_modules(self):
        self.assertIs(SentenceParadigm, SplitSentenceParadigm)
        self.assertIs(
            LockedInSentenceReadingParadigm,
            SplitLockedInParadigm,
        )
        self.assertIs(ReadingParadigm, SplitReadingParadigm)
        self.assertIs(ListeningParadigm, SplitListeningParadigm)
        self.assertIs(RelaxingNewsParadigm, SplitNewsParadigm)
        self.assertEqual(
            BaseParadigm.__module__,
            "experiment_paradigm.core.base",
        )

    def test_cli_compatibility_layer_reexports_split_commands(self):
        self.assertIs(compatibility_locked_parser, parse_locked_in_args)
        self.assertIs(compatibility_news_main, main_relaxing_news)

    def test_news_default_is_repository_relative(self):
        args = parse_relaxing_news_args([])

        self.assertEqual(args.news, Path("stimuli/news/2026_07_23.md"))
        self.assertFalse(args.news.is_absolute())
        self.assertEqual(
            args.audio_dir,
            Path(
                "assets/news_audio/2026_07_23/"
                "zh-CN-YunyangNeural"
            ),
        )
        self.assertFalse(args.audio_dir.is_absolute())

    def test_shared_duration_validation(self):
        validate_duration_range("rest", 5.0, 6.0)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            validate_duration_range("rest", -1.0, 6.0)
        with self.assertRaisesRegex(ValueError, "minimum"):
            validate_duration_range("rest", 7.0, 6.0)

    def test_repository_scripts_remain_thin_entry_points(self):
        scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
        for path in scripts_dir.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            classes = [
                node for node in tree.body if isinstance(node, ast.ClassDef)
            ]
            functions = [
                node
                for node in tree.body
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
            ]
            self.assertEqual(classes, [], path.name)
            self.assertEqual(functions, [], path.name)


if __name__ == "__main__":
    unittest.main()
