"""Create {name} table."""
import os
import sys
import argparse
from tabulate import tabulate

def table():
    """Create table."""
    header = [""],
    content = []
    content.append([""])

    return header, content


def parse_args(*argv):
    """Parse args."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--show', action="store_true")
    return parser.parse_args(argv)


def main(*argv):
    """Main."""
    args = parse_args(*argv)
    header, tbl = table()
    if args.show:
        print(tabulate(tbl, headers=header, tablefmt="simple"))
    else:
        with open(os.path.splitext(os.path.basename(__file__))[0], 'w') as f:
            f.write(tabulate(tbl, headers=header, tablefmt="latex")
                    .replace('\$', '$')
                    .replace('\\textbackslash{{}}', '\\'))


if __name__ == '__main__':
    main(*sys.argv[1:])
