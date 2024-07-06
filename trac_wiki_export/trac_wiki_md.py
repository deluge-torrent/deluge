from pathlib import Path
import sys

import migrate


def main(wiki_dir):
    pagenames = [page.name for page in wiki_dir.iterdir()]
    conv_help = migrate.WikiConversionHelper(pagenames=pagenames)

    for wiki_page in wiki_dir.iterdir():
        conv_help.set_wikipage_paths(wiki_page.name)
        print("Converting wiki page:", wiki_page.name)

        md_text = migrate.trac2markdown(wiki_page.read_text(), ".", conv_help)
        out_filepath = Path("md_output", conv_help._wiki_path)
        out_filepath = out_filepath.with_suffix(".md")
        out_filepath.parent.mkdir(parents=True, exist_ok=True)
        out_filepath.write_text(md_text)


if __name__ == "__main__":
    wiki_dir = Path(sys.argv[1])
    main(wiki_dir)
