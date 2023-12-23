"""Report generator."""
import os
import sys
import argparse
import shutil
import subprocess
import datetime
import re

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
REPORT_DIR = os.path.dirname(THIS_DIR)
TEMPLATE_DIR = os.path.join(REPORT_DIR, 'template')
INIT_TEMPLATE = os.path.join(TEMPLATE_DIR, "skel")
CHAPTER_TEMPLATE = os.path.join(TEMPLATE_DIR, "chapter")
FIGURE_TEMPLATE = os.path.join(TEMPLATE_DIR, 'figure.py')
TABLE_TEMPLATE = os.path.join(TEMPLATE_DIR, 'table.py')
INDEXFILE = 'report.tex'
SED = ['gsed' if sys.platform == 'darwin' else 'sed']
GIT = ['git']


def _indexfile(path='.'):
    """Get name of index texfile."""
    path = os.path.abspath(path)
    while path and path != '/':
        indexfile = os.path.abspath('/'.join([path, INDEXFILE]))
        if os.path.exists(indexfile):
            return indexfile
        path = os.path.dirname(path)
    return None


def _get_root():
    return os.path.dirname(_indexfile())


def _is_inside_report():
    """Check if inside report directory."""
    return _indexfile() is not None


def _is_inside_chapter():
    """Check if inside chapter directory."""
    return _indexfile('..') is not None


def _git_sha1():
    """Get git sha1."""
    try:
        return subprocess.check_output(
            GIT + ['rev-parse', '--short', 'HEAD'],
            universal_newlines=True).strip()
    except subprocess.CalledProcessError:
        return None


def _git_reference():
    """Get hash of git directory."""
    try:
        tag = subprocess.check_output(
            GIT + ['tag', '--points-at', 'HEAD'],
            universal_newlines=True).strip()
    except subprocess.CalledProcessError:
        return None
    if tag:
        return tag
    return _git_sha1()


def _sed_replace(file_, match, replacement):
    """Run sed, inplace on file, to replace string."""
    subprocess.run(SED + ['-i', 's/' + match + '/' + replacement + '/',
                   file_])


def _sed_remove(file_, match):
    """Run sed, inplace on file, to remove string."""
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


def add_table(*argv):
    """Add new python latex table."""
    assert _is_inside_report(), "Must be inside report directory"
    assert _is_inside_chapter(), "Must be inside chapter directory"
    argparser = argparse.ArgumentParser()
    argparser.add_argument("names", help="Table names", nargs='+')
    args = argparser.parse_args(argv)
    for name in args.names:
        filename = name + '.py'
        if os.path.exists(filename):
            print("Table exists: ", name)
            continue
        with open(TABLE_TEMPLATE, 'r') as input_file:
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
    shutil.move("{newname}/{name}.tex".format(name=args.name, newname=args.newname),
                "{newname}/{newname}.tex".format(newname=args.newname))
    _sed_replace(_indexfile(),
                 _newchapter(args.name),
                 _newchapter(args.newname))
    print("Renamed chapter ", args.name, ' -> ', args.newname)


def get_filename():
    """Get the export filename."""
    with open(_indexfile(), 'r') as f:
        name_template = f.readline().strip('%').strip()
    filename = name_template.format(
        ref=_git_reference(),
        sha1=_git_sha1(),
        date=datetime.date.today().strftime('%Y-%m-%d'),
        time=datetime.datetime.now().strftime("%H:%M"),
        miltime=datetime.datetime.now().strftime("%H%M")
    )
    return filename


def export(*argv):
    """Export report."""
    assert _is_inside_report(), "Must be inside report directory"
    filename = get_filename()
    dst = os.path.abspath('/'.join(
        [os.path.dirname(_indexfile()), filename + '.pdf']))
    src = os.path.splitext(_indexfile())[0] + '.pdf'
    shutil.copyfile(src, dst)


def tag(*argv):
    """Tag git repo."""
    tag = get_filename()
    subprocess.check_output(
        GIT + ['tag', '-a', '-m', tag, tag, 'HEAD'],
        universal_newlines=True).strip()
    print("Set tag", tag)


def _get_chapters():
    assert _is_inside_report(), "Must be inside report directory"
    chapters = []
    with open(_indexfile()) as handle:
        for row in handle:
            m = re.search(r"newchapter{([^}]+)}", row)
            if m:
                chapters.append(m[1])
    return chapters


def list_chapters(*argv):
    assert _is_inside_report(), "Must be inside report directory"
    for chapter in _get_chapters():
        print(chapter)


def list_chapterfiles(*argv):
    assert _is_inside_report(), "Must be inside report directory"
    for chapter in _get_chapters():
        print(f"{chapter}/{chapter}.tex")


def list_texfiles(*argv):
    assert _is_inside_report(), "Must be inside report directory"
    print(os.path.relpath(_indexfile()))
    root = _get_root()
    for chapter in _get_chapters():
        print(os.path.relpath(f"{root}/{chapter}/{chapter}.tex"))
