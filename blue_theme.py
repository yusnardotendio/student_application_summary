# my_blue_theme.py

from __future__ import annotations
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes
from collections.abc import Iterable

# Step 1: Define your custom color palette
custom_blue = colors.Color(
    name="custom_blue",
    c50="#e4eef8",
    c100="#c9dcf2",
    c200="#9cc0e6",
    c300="#70a4da",
    c400="#4d92d2",
    c500="#4889CE",  # your main color
    c600="#3f7cb9",
    c700="#366fa4",
    c800="#2d628f",
    c900="#24557a",
    c950="#1b4865",
)

# Step 2: Create a custom theme based on Base or Soft
class BlueTheme(Base):
    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = custom_blue,
        secondary_hue: colors.Color | str = custom_blue,
        neutral_hue: colors.Color | str = colors.gray,
        spacing_size: sizes.Size | str = sizes.spacing_md,
        radius_size: sizes.Size | str = sizes.radius_md,
        text_size: sizes.Size | str = sizes.text_md,
        font: fonts.Font | str | Iterable[fonts.Font | str] = (
            fonts.LocalFont("Montserrat"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif",
        ),
        font_mono: fonts.Font | str | Iterable[fonts.Font | str] = (
            fonts.LocalFont("IBM Plex Mono"),
            "ui-monospace",
            "Consolas",
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )
        self.name = "blue_theme"

        super().set(
            background_fill_primary="*neutral_50",
            block_label_background_fill="*primary_700",
            block_border_width="1px",
            block_border_color="*primary_200",
            block_label_text_color="*primary_500",
            button_primary_background_fill="*custom_blue",
            button_primary_background_fill_hover="*primary_400",
            button_primary_text_color="white",
            slider_color="*custom_blue",
        )
