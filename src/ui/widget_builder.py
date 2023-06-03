from pygame import Color
from pygame.freetype import Font, SysFont

from ..sprites import SpriteKeeper, SpriteSheet
from .blueprint import (
    AtlasBlueprint,
    DialogueBlueprint,
    FontBlueprint,
    ItemBlueprint,
    PanelBlueprint,
    SelectionBlueprint,
    SelectorBlueprint,
    TextboxBlueprint,
    size_to_tuple,
)
from .dialogue import Dialogue
from .observer import ListPublisher
from .panel import Panel, PanelBuilder
from .selector import Selection, Selector
from .textbox import Textbox


class WidgetBuilder:

    def __init__(self,
                 keeper: SpriteKeeper,
                 panel_path: str | None = None,
                 ) -> None:

        self._keeper = keeper
        self._panel_builder = PanelBuilder(keeper, panel_path)

    def build_textbox(self, blueprint: TextboxBlueprint) -> Textbox:
        bg = self.build_panel(blueprint.bg)
        font = self.build_font(blueprint.font)

        part_size = size_to_tuple(blueprint.bg.part_size)
        padding = (*part_size, *part_size)

        return Textbox(text=blueprint.text,
                       bg=bg,
                       trigger=blueprint.trigger,
                       padding=padding,
                       font=font,
                       editable=blueprint.editable,
                       closeable=blueprint.closeable)

    def build_dialogue(self, blueprint: DialogueBlueprint) -> Dialogue:
        bg = self.build_panel(blueprint.bg)
        font = self.build_font(blueprint.font)

        portrait = self.build_atlas(blueprint.portrait).extract_whole()
        part_size = size_to_tuple(blueprint.bg.part_size)
        padding = (*part_size, *part_size)
        spacing = size_to_tuple(blueprint.spacing)

        return Dialogue(text=blueprint.text,
                        portrait=portrait,
                        header=blueprint.header,
                        bg=bg,
                        trigger=blueprint.trigger,
                        padding=padding,
                        spacing=spacing,
                        font=font,
                        editable=blueprint.editable,
                        closeable=blueprint.closeable)

    def build_selector(self, blueprint: SelectorBlueprint) -> Selector:
        def create_item(ib: ItemBlueprint) -> object:
            # TODO
            return ib.obj

        def create_selection(sb: SelectionBlueprint) -> Selection:
            s = Selection()
            s.image = self.build_atlas(sb.image).extract_whole()
            s.text = sb.text
            s.header = sb.header
            s.item = create_item(sb.item)
            return s

        data = [create_selection(sb) for sb in blueprint.data.values()]
        data_source: ListPublisher[Selection] = ListPublisher(data)

        bg = self.build_panel(blueprint.bg)

        part_size = size_to_tuple(blueprint.bg.part_size)
        padding = (*part_size, *part_size)
        spacing = size_to_tuple(blueprint.spacing)
        font = self.build_font(blueprint.font)
        selection_size = size_to_tuple(blueprint.selection_size)

        return Selector(data_source=data_source,
                        bg=bg,
                        trigger=blueprint.trigger,
                        padding=padding,
                        columns=blueprint.columns,
                        spacing=spacing,
                        font=font,
                        selection_size=selection_size,
                        closeable=blueprint.closeable)

    def build_panel(self, blueprint: PanelBlueprint) -> Panel:
        size = size_to_tuple(blueprint.size)
        return self._panel_builder.build_panel(size=size,
                                               path=blueprint.source,
                                               alpha=blueprint.alpha)

    def build_font(self, blueprint: FontBlueprint) -> Font:
        font = SysFont(blueprint.name, blueprint.size)
        font.fgcolor = Color(blueprint.color)
        return font

    def build_atlas(self, blueprint: AtlasBlueprint) -> SpriteSheet:
        return self._keeper.sprite(blueprint.source, blueprint.alpha)
