import os
from pytest import fixture, raises, warns
import warnings
from typing import Generator

from utz.environ import env, OnConflict, OnExit, EnvPatchConflict


@fixture
def clean_env() -> Generator[None, None, None]:
    """Fixture to preserve and restore original environment."""
    original = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


class TestEnvBasics:
    def test_singleton(self):
        """Test that Env is a proper singleton."""
        from utz.environ import Env
        assert env is Env()
        assert Env() is Env()

    def test_dict_interface(self, clean_env):
        """Test basic dictionary-like operations."""
        env["TEST_VAR"] = "value1"
        try:
            assert env["TEST_VAR"] == "value1"
            assert "TEST_VAR" in env
            assert env.get("TEST_VAR") == "value1"
            assert env.get("NONEXISTENT", "default") == "default"
        finally:
            del env["TEST_VAR"]
        assert "TEST_VAR" not in env

        # Test iteration
        env.update({"A": "1", "B": "2"})
        assert set(env.keys()) >= {"A", "B"}
        assert set(env.items()) >= {("A", "1"), ("B", "2")}
        assert set(env.values()) >= {"1", "2"}

    def test_type_coercion(self, clean_env):
        """Test that values are properly converted to strings."""
        env["INT"] = 42
        env["BOOL"] = True
        env["FLOAT"] = 3.14

        assert env["INT"] == "42"
        assert env["BOOL"] == "True"
        assert env["FLOAT"] == "3.14"


class TestContextManager:
    def test_basic_context(self, clean_env):
        """Test basic context manager functionality."""
        assert "TEST_VAR" not in env

        with env(TEST_VAR="temporary"):
            assert env["TEST_VAR"] == "temporary"

        assert "TEST_VAR" not in env

    def test_dict_syntax(self, clean_env):
        """Test dictionary syntax for context manager."""
        with env({"TEST_VAR": "value1", "TEST_VAR2": "value2"}):
            assert env["TEST_VAR"] == "value1"
            assert env["TEST_VAR2"] == "value2"

        assert "TEST_VAR" not in env
        assert "TEST_VAR2" not in env

    def test_kwargs_syntax(self, clean_env):
        """Test kwargs syntax for context manager."""
        with env(TEST_VAR="value1", TEST_VAR2="value2"):
            assert env["TEST_VAR"] == "value1"
            assert env["TEST_VAR2"] == "value2"

        assert "TEST_VAR" not in env
        assert "TEST_VAR2" not in env

    def test_mixed_syntax_error(self, clean_env):
        """Test that mixing dict and kwargs raises an error."""
        with raises(ValueError):
            with env({"TEST": "value"}, OTHER="value"):
                pass

    def test_existing_var_restore(self, clean_env):
        """Test that existing variables are properly restored."""
        env["EXISTING"] = "original"

        with env(EXISTING="temporary"):
            assert env["EXISTING"] == "temporary"

        assert env["EXISTING"] == "original"

    def test_multiple_nested_contexts(self, clean_env):
        """Test nested context managers."""
        with env(VAR1="outer1", VAR2="outer2"):
            assert env["VAR1"] == "outer1"
            assert env["VAR2"] == "outer2"

            with env(VAR1="inner1", VAR3="inner3"):
                assert env["VAR1"] == "inner1"
                assert env["VAR2"] == "outer2"
                assert env["VAR3"] == "inner3"

            assert env["VAR1"] == "outer1"
            assert env["VAR2"] == "outer2"
            assert "VAR3" not in env

        assert "VAR1" not in env
        assert "VAR2" not in env


class TestConflictHandling:
    def test_error_on_conflict(self, clean_env):
        """Test that conflicts raise an error by default."""
        with raises(EnvPatchConflict, match="TEST_VAR"):
            with env(TEST_VAR="original"):
                env["TEST_VAR"] = "modified"

        assert "TEST_VAR" not in env

    def test_warn_on_conflict(self, clean_env):
        """Test warning behavior for conflicts."""
        with warnings.catch_warnings(record=True) as w:
            with env(TEST_VAR="original", _on_conflict=OnConflict.WARN):
                env["TEST_VAR"] = "modified"

            assert len(w) == 1
            assert issubclass(w[0].category, RuntimeWarning)
            assert "TEST_VAR" in str(w[0].message)

    def test_ignore_conflict(self, clean_env):
        """Test ignore behavior for conflicts."""
        with env(TEST_VAR="original", _on_conflict=OnConflict.IGNORE):
            env["TEST_VAR"] = "modified"
            # Should not raise or warn

    def test_unmodified_always_reset(self, clean_env):
        """Test that unmodified variables are always reset regardless of on_exit."""
        with env(MODIFIED="value1", UNMODIFIED="value2", on_conflict=OnConflict.IGNORE, on_exit=OnExit.SKIP):
            env["MODIFIED"] = "changed"
            assert env["UNMODIFIED"] == "value2"

        assert "UNMODIFIED" not in env  # Should always be reset
        assert env["MODIFIED"] == "changed"

    def test_skip_conflicted(self, clean_env):
        """Test that conflicted variables can be skipped on exit."""
        with (
            warns(RuntimeWarning, match="TEST_VAR"),
            env(TEST_VAR="original", on_conflict=OnConflict.WARN, on_exit=OnExit.SKIP)
        ):
            env["TEST_VAR"] = "modified"

        assert env["TEST_VAR"] == "modified"

    def test_reset_conflicted(self, clean_env):
        """Test that conflicted variables can be reset on exit."""
        env["TEST_VAR"] = "initial"

        with env(TEST_VAR="original", on_conflict=OnConflict.IGNORE, on_exit=OnExit.RESET):
            env["TEST_VAR"] = "modified"

        assert env["TEST_VAR"] == "initial"
