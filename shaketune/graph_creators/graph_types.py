# Shake&Tune: 3D printer analysis tools
#
# Copyright (C) 2024 Félix Boisselier <felix@fboisselier.fr> (Frix_x on Discord)
# Licensed under the GNU General Public License v3.0 (GPL-3.0)
#
# File: graph_types.py
# Description: Type-safe enum for graph types used throughout Shake&Tune

from enum import Enum


class GraphType(str, Enum):
    """Type-safe graph type identifiers.

    This enum inherits from str to allow direct comparison with string values
    and seamless JSON serialization. Use these constants instead of string
    literals to catch typos at import time rather than runtime.

    Example:
        >>> graph_type = GraphType.INPUT_SHAPER
        >>> graph_type == 'input shaper'
        True
        >>> graph_type.value
        'input shaper'
    """

    AXES_MAP = 'axes map'
    BELTS_COMPARISON = 'belts comparison'
    INPUT_SHAPER = 'input shaper'
    VIBRATIONS_PROFILE = 'vibrations profile'
    STATIC_FREQUENCY = 'static frequency'

    @classmethod
    def from_string(cls, value: str) -> 'GraphType':
        """Convert a string to GraphType enum.

        Args:
            value: String representation of graph type

        Returns:
            Corresponding GraphType enum value

        Raises:
            ValueError: If the string doesn't match any graph type
        """
        for member in cls:
            if member.value == value:
                return member
        valid_types = ', '.join(f"'{m.value}'" for m in cls)
        raise ValueError(f"Invalid graph type '{value}'. Valid types are: {valid_types}")

    @property
    def folder_name(self) -> str:
        """Get the folder name associated with this graph type.

        Returns:
            Folder name for storing results of this graph type
        """
        folder_map = {
            GraphType.AXES_MAP: 'axes_map',
            GraphType.BELTS_COMPARISON: 'belts',
            GraphType.INPUT_SHAPER: 'input_shaper',
            GraphType.VIBRATIONS_PROFILE: 'vibrations',
            GraphType.STATIC_FREQUENCY: 'static_freq',
        }
        return folder_map[self]
