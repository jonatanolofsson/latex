"""Report generator."""
import os
import sys
import argparse
import shutil
import subprocess

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
REPORT_DIR = os.path.dirname(THIS_DIR)
TEMPLATE_DIR = os.path.join(REPORT_DIR, 'template')
INIT_TEMPLATE = os.path.join(TEMPLATE_DIR, "skel")
CHAPTER_TEMPLATE = os.path.join(TEMPLATE_DIR, "chapter")
FIGURE_TEMPLATE = os.path.join(TEMPLATE_DIR, 'figure.py')
INDEXFILE = 'report.tex'
SED = ['gsed' if sys.platform == 'darwin' else 'sed']
GIT = ['git']


def _indexfile(path='.'):
    """Get name of index texfile."""
    path = os.path.abspath(path)
    while path:
        indexfile = os.path.abspath('/'.join([path, INDEXFILE]))
        if os.path.exists(indexfile):
            return indexfile
        path = os.path.dirname(path)
    return None


def _is_inside_report():
    """Check if inside report directory."""
    return _indexfile() is not None


def _is_inside_chapter():
    """Check if inside chapter directory."""
    return _indexfile('..') is not None


def _git_reference(short=True):
    """Get hash of git directory."""
    tag = subprocess.check_output(
        GIT + ['tag', '--points-at', 'HEAD'],
        universal_newlines=True).strip()
    if not tag:
        tag = subprocess.check_output(
            GIT + ['rev-parse', '--short', 'HEAD'],
            universal_newlines=True).strip()
    return tag


def _sed_replace(file_, match, replacement):
    """Run sed, inplace on file, to replace string."""
    subprocess.run(SED + ['-i', 's/' + match + '/' + replacement + '/',
                   file_])


def _sed_remove(file_, match):
    """Run sed, inplace on file, to replace string."""
    subprocess.run(SED + ['-i', '/' + match + '/d', file_])


def _insert(file_, tag, string, after_marker=False):
    """Add text at marker in file."""
    replacement = '%%::' + tag + '::%%\\n' + string if after_marker \
        else string + '\\n%%::' + tag + '::%%'
    _sed_replace(file_, '^%%::' + tag + '::%%$', replacement)


def _newchapter(name):
    """Return tex tag for newchapter."""
    return '\\\\newchapter{{{}}}'.format(name)


def init(*argv):
    """Create a new report."""
    argparser = argparse.ArgumentParser()
    argparser.add_argument("name", help="Directory name")
    args = argparser.parse_args(argv)
    assert not _is_inside_report(), "Recursion detected"
    assert not os.path.exists(args.name), "Directory exists, cannot initialize"
    print('Initializing report "{}"'.format(args.name))
    shutil.copytree(INIT_TEMPLATE, args.name)


def add_chapter(*argv):
    """Add chapter."""
    assert _is_inside_report(), "Must be inside report directory"
    argparser = argparse.ArgumentParser()
    argparser.add_argument("names", help="Chapter names", nargs='+')
    argparser.add_argument('--appendix', "-a",
                           help="Insert chapter as appendix",
                           action="store_true")
    args = argparser.parse_args(argv)
    for name in args.names:
        if os.path.exists(name):
            print("Chapter exists: ", name)
            continue
        marker = 'appendices' if args.appendix else "chapters"
        os.makedirs(name)
        with open(os.path.join(CHAPTER_TEMPLATE, 'chapter.tex'), 'r') \
                as input_file:
            with open(os.path.join(name, name + '.tex'), 'w') as output_file:
                output_file.write(input_file.read().format(
                    name=name, capname=name.capitalize()))
        _insert(_indexfile(), marker, '\\\\newchapter{{{}}}'.format(name))
        print("Add appendix" if args.appendix else "Add chapter", name)


def add_figure(*argv):
    """Add new python figure."""
    assert _is_inside_report(), "Must be inside report directory"
    assert _is_inside_chapter(), "Must be inside chapter directory"
    argparser = argparse.ArgumentParser()
    argparser.add_argument("names", help="Figure names", nargs='+')
    args = argparser.parse_args(argv)
    for name in args.names:
        filename = name + '.py'
        if os.path.exists(filename):
            print("Figure exists: ", name)
            continue
        with open(FIGURE_TEMPLATE, 'r') as input_file:
            with open(filename, 'w') as output_file:
                output_file.write(input_file.read().format(name=name))


def remove_chapter(*argv):
    """Remove chapter."""
    assert _is_inside_report(), "Must be inside report directory"
    argparser = argparse.ArgumentParser()
    argparser.add_argument("name", help="Chapter name")
    args = argparser.parse_args(argv)
    assert os.path.exists(args.name), "Chapter does not exist"
    shutil.rmtree(args.name)
    _sed_remove(_indexfile(), '^' + _newchapter(args.name) + '$')
    print("Removed chapter ", args.name)


def rename_chapter(*argv):
    """Rename chapter."""
    assert _is_inside_report(), "Must be inside report directory"
    argparser = argparse.ArgumentParser()
    argparser.add_argument("name", help="Chapter name")
    argparser.add_argument("newname", help="New chapter name")
    args = argparser.parse_args(argv)
    assert os.path.exists(args.name), "Chapter does not exist"
    shutil.move(args.name, args.newname)
    _sed_replace(_indexfile(),
                 _newchapter(args.name),
                 _newchapter(args.newname))
    print("Renamed chapter ", args.name, ' -> ', args.newname)


def export(*argv):
    """Export report."""
    assert _is_inside_report(), "Must be inside report directory"
    with open(_indexfile(), 'r') as f:
        filename = f.readline().strip('%').strip()
    dst = os.path.abspath('/'.join([os.path.dirname(_indexfile()), filename]))
    dst += '_' + _git_reference() + '.pdf'
    src = os.path.splitext(_indexfile())[0] + '.pdf'
    shutil.copyfile(src, dst)
