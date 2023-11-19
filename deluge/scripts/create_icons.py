#!/usr/bin/python3
#
# Create Deluge PNG icons from SVG
#
# Required image tools:
#  * rsvg-convert
#  * convert (ImageMagik)
#  * oxipng
#  * pngquant
#
import shutil
import subprocess
from pathlib import Path

from dataclasses import dataclass, field


@dataclass
class IconPack:
    name: str
    dir: Path
    icon_sizes: list[int]
    panel_sizes: list[int]
    ico_sizes: list[int]
    pixmaps_dir: Path = field(init=False)
    theme_dir: Path = field(init=False)
    theme_svg: Path = field(init=False)
    theme_pngs: dict[int, Path] = field(init=False)
    logo_svg: Path = field(init=False)
    logo_ico: Path = field(init=False)
    logo_png: Path = field(init=False)

    def __post_init__(self):
        self.pixmaps_dir = self.dir / 'pixmaps'
        self.logo_svg = self.pixmaps_dir / f'{self.name}.svg'
        self.logo_ico = self.pixmaps_dir / f'{self.name}.ico'
        self.logo_png = self.pixmaps_dir / f'{self.name}.png'

        self.theme_dir = self.dir / 'icons' / 'hicolor'
        self.theme_svg = self.theme_dir / 'scalable' / 'apps' / f'{self.name}.svg'
        self.theme_pngs = self.create_theme_pngs_paths(
            self.name, self.icon_sizes, self.theme_dir
        )

    @staticmethod
    def create_theme_pngs_paths(name, icon_sizes, out_dir):
        return {
            size: out_dir / f'{size}x{size}' / 'apps' / f'{name}.png'
            for size in icon_sizes
        }


@dataclass
class WebIconPack:
    name: str
    dir: Path
    icon_sizes: list[int]
    favicon_sizes: list[int]
    icons_dir: Path = field(init=False)
    touch: Path = field(init=False)
    favicon: Path = field(init=False)

    def __post_init__(self):
        self.icons_dir = self.dir / 'icons'
        self.touch = self.icons_dir / f'{self.name}-apple-180.png'
        self.favicon = self.icons_dir / 'favicon.ico'


def convert_svg_to_png(svg_file, png_file, size, background_color=None):
    rsvg_options = [
        '-w',
        str(size),
        '-h',
        str(size),
        '-o',
        png_file,
    ]
    rsvg_options + ['-b', {background_color}] if background_color else []

    subprocess.run(['rsvg-convert'] + rsvg_options + [svg_file], check=True)


def compress_png(png_file):
    subprocess.run(
        ['pngquant', '--quality=70-95', '--ext', '.png', '--force', png_file],
        check=True,
    )
    subprocess.run(['oxipng', png_file], check=True)


def create_panel_icons(icon_pack, sizes):
    for size in sizes:
        app_png = icon_pack[size]
        panel_png = app_png.with_name(f'{app_png.stem}-panel.png')
        shutil.copyfile(app_png, panel_png)


def create_hicolor_icons(svg_icon, icon_pack):
    """Convert SVG icon to hicolor PNG icons."""
    for size, png_file in icon_pack.items():
        png_file.parent.mkdir(parents=True, exist_ok=True)
        convert_svg_to_png(svg_icon, png_file, size)
        compress_png(png_file)


def create_ico_icon(icon_pack, sizes, ico_file):
    infiles = [icon_pack[size] for size in sizes]
    ico_file.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(['convert', *infiles, ico_file], check=True)


def create_hicolor_svg(src_svg, dest_svg):
    dest_svg.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_svg, dest_svg)


def create_mini_icons(pixmaps_dir):
    pixmap_svgs = pixmaps_dir.glob('*.svg')

    for svg_file in pixmap_svgs:
        png_file = pixmaps_dir / f'{svg_file.stem}16.png'
        convert_svg_to_png(svg_file, png_file, 16)
        compress_png(png_file)


def create_logo(deluge_png, pixmap_png):
    pixmap_png.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(deluge_png, pixmap_png)


def create_web_status_icons(src_dir: Path, dest_dir: Path):
    """Web UI status icons from 16px icons."""
    pngs_16px = src_dir.glob('*16.png')
    dest_dir.mkdir(parents=True, exist_ok=True)
    for path in pngs_16px:
        if path.stem.startswith('tracker'):
            continue
        new_name = path.stem.replace('16', '') + '.png'
        shutil.copyfile(path, dest_dir / new_name)


def create_touch_icon(svg_file, png_file, size):
    """Web icons with background color for Apple or Android"""
    png_file.parent.mkdir(parents=True, exist_ok=True)
    convert_svg_to_png(svg_file, png_file, size, background_color='#599EEE')
    compress_png(png_file)


def create_web_icons(app_pngs, sizes, dest_dir):
    dest_dir.mkdir(parents=True, exist_ok=True)
    for size in sizes:
        app_png = app_pngs[size]
        web_png = dest_dir / f'{app_png.stem}-{size}.png'
        shutil.copyfile(app_png, web_png)


def main():
    DATA_DIR = Path.cwd() / 'deluge' / 'ui' / 'data'
    if not DATA_DIR.is_dir():
        exit(f'No path to UI data dir: {DATA_DIR}')

    # Create Deluge UI icons
    ICON_PACK_SIZES = [16, 22, 24, 32, 36, 48, 64, 72, 96, 128, 192, 256, 512]
    PANEL_ICON_SIZES = [16, 22, 24]
    ICO_ICON_SIZES = [16, 32, 48, 64, 128, 256]
    ui_icons = IconPack(
        name='deluge',
        dir=DATA_DIR,
        icon_sizes=ICON_PACK_SIZES,
        panel_sizes=PANEL_ICON_SIZES,
        ico_sizes=ICO_ICON_SIZES,
    )

    # Theme icons for GTK
    create_hicolor_icons(ui_icons.logo_svg, ui_icons.theme_pngs)
    create_hicolor_svg(ui_icons.logo_svg, ui_icons.theme_svg)
    create_mini_icons(ui_icons.pixmaps_dir)
    # Panel icon for systray
    create_panel_icons(ui_icons.theme_pngs, ui_icons.panel_sizes)

    # Deluge logos
    create_ico_icon(ui_icons.theme_pngs, ui_icons.ico_sizes, ui_icons.logo_ico)
    create_logo(ui_icons.theme_pngs[48], ui_icons.logo_png)

    # Web UI Icons
    WEB_ICON_SIZES = [32, 192, 512]
    FAVICON_SIZES = [16, 32, 48]
    web_icons = WebIconPack(
        name='deluge',
        dir=DATA_DIR / '..' / 'web',
        icon_sizes=WEB_ICON_SIZES,
        favicon_sizes=FAVICON_SIZES,
    )
    create_web_icons(ui_icons.theme_pngs, web_icons.icon_sizes, web_icons.icons_dir)
    create_web_status_icons(ui_icons.pixmaps_dir, web_icons.icons_dir)
    create_touch_icon(ui_icons.logo_svg, web_icons.touch, 180)
    create_ico_icon(ui_icons.theme_pngs, web_icons.favicon_sizes, web_icons.favicon)


if __name__ == '__main__':
    main()
