"""Pure edit ops on immutable Timeline."""
from .caption import op_caption_add, op_caption_remove
from .cut import op_cut
from .keep import op_keep
from .speed import op_speed

__all__ = ["op_caption_add", "op_caption_remove", "op_cut", "op_keep", "op_speed"]
