# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# Tests for graph_types.py

import pytest

from shaketune.graph_creators.graph_types import GraphType


class TestGraphType:
    """Tests for GraphType enum."""

    def test_all_types_exist(self):
        """Test that all expected graph types are defined."""
        expected_types = [
            'AXES_MAP',
            'BELTS_COMPARISON',
            'INPUT_SHAPER',
            'VIBRATIONS_PROFILE',
            'STATIC_FREQUENCY',
        ]

        for type_name in expected_types:
            assert hasattr(GraphType, type_name), f'GraphType should have {type_name}'

    def test_string_values(self):
        """Test that enum values are correct strings."""
        assert GraphType.AXES_MAP.value == 'axes map'
        assert GraphType.BELTS_COMPARISON.value == 'belts comparison'
        assert GraphType.INPUT_SHAPER.value == 'input shaper'
        assert GraphType.VIBRATIONS_PROFILE.value == 'vibrations profile'
        assert GraphType.STATIC_FREQUENCY.value == 'static frequency'

    def test_string_comparison(self):
        """Test that GraphType can be compared to strings."""
        assert GraphType.INPUT_SHAPER == 'input shaper'
        assert GraphType.AXES_MAP == 'axes map'

    def test_from_string_valid(self):
        """Test from_string with valid values."""
        assert GraphType.from_string('axes map') == GraphType.AXES_MAP
        assert GraphType.from_string('input shaper') == GraphType.INPUT_SHAPER
        assert GraphType.from_string('belts comparison') == GraphType.BELTS_COMPARISON

    def test_from_string_invalid(self):
        """Test from_string raises ValueError for invalid input."""
        with pytest.raises(ValueError) as exc_info:
            GraphType.from_string('invalid type')

        assert 'Invalid graph type' in str(exc_info.value)
        assert 'invalid type' in str(exc_info.value)

    def test_folder_name_property(self):
        """Test folder_name property returns correct values."""
        assert GraphType.AXES_MAP.folder_name == 'axes_map'
        assert GraphType.BELTS_COMPARISON.folder_name == 'belts'
        assert GraphType.INPUT_SHAPER.folder_name == 'input_shaper'
        assert GraphType.VIBRATIONS_PROFILE.folder_name == 'vibrations'
        assert GraphType.STATIC_FREQUENCY.folder_name == 'static_freq'

    def test_all_types_have_folder_names(self):
        """Test that all graph types have folder names defined."""
        for graph_type in GraphType:
            folder = graph_type.folder_name
            assert folder is not None
            assert isinstance(folder, str)
            assert len(folder) > 0

    def test_enum_iteration(self):
        """Test that GraphType can be iterated."""
        types = list(GraphType)
        assert len(types) == 5

    def test_enum_is_hashable(self):
        """Test that GraphType values can be used in sets/dicts."""
        type_set = {GraphType.AXES_MAP, GraphType.INPUT_SHAPER}
        assert len(type_set) == 2

        type_dict = {GraphType.AXES_MAP: 'test'}
        assert type_dict[GraphType.AXES_MAP] == 'test'
