"""Load and commit Amulet chunks while placing blocks."""

from __future__ import annotations

from amulet.api.chunk import Chunk
from amulet.api.errors import ChunkDoesNotExist
from amulet.level.formats.anvil_world import AnvilFormat

from helpers.structure_tokens import ParsedToken
from helpers.worldgen_block_updates import place_worldgen_block


class WorldgenChunkWriter:
    def __init__(self, level: AnvilFormat, dimension: str) -> None:
        self._level = level
        self._dimension = dimension
        self._current_chunk: Chunk | None = None
        self._last_coords: tuple[int, int] | None = None

    def place(
        self,
        global_x: int,
        world_y: int,
        global_z: int,
        block,
        parsed: ParsedToken,
    ) -> None:
        chunk_x = global_x // 16
        chunk_z = global_z // 16
        chunk_coords = (chunk_x, chunk_z)

        if chunk_coords != self._last_coords:
            self.flush()

            try:
                self._current_chunk = self._level.load_chunk(chunk_x, chunk_z, self._dimension)
            except ChunkDoesNotExist:
                self._current_chunk = Chunk(chunk_x, chunk_z)

            self._last_coords = chunk_coords

        if self._current_chunk is None:
            raise RuntimeError("chunk writer failed to load a chunk")

        place_worldgen_block(
            self._current_chunk,
            local_x=global_x % 16,
            world_y=world_y,
            local_z=global_z % 16,
            world_x=global_x,
            world_z=global_z,
            block=block,
            parsed=parsed,
        )
        self._current_chunk.changed = True

    def flush(self) -> None:
        if self._current_chunk is not None:
            self._level.commit_chunk(self._current_chunk, self._dimension)
            self._current_chunk = None
            self._last_coords = None
