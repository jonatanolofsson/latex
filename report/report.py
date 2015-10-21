""" Report generator """
import os
import argparse
import shutil
import subprocess

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
REPORT_DIR = os.path.dirname(THIS_DIR)
TEMPLATE_DIR = os.path.join(REPORT_DIR, 'template')
INIT_TEMPLATE = os.path.join(TEMPLATE_DIR, "skel")
CHAPTER_TEMPLATE = os.path.join(TEMPLATE_DIR, "chapter")
DEFAULT_INDEXFILE = 'report.tex'
SED = ['sed']


def _indexfile():
    """ Get name of index texfile """
    texfiles = [f for f in os.listdir() if f.endswith('.tex')]
    if len(texfiles) == 1:
        return texfiles[0]
    else:
        if len(texfiles) > 1:
            assert DEFAULT_INDEXFILE in texfiles, "Multiple texfiles found, but no default"
        return DEFAULT_INDEXFILE


def _is_inside_report():
    """ Check if inside report directory """
    return os.path.exists(_indexfile())


def _sed_replace(file_, match, replacement):
    """ Run sed, inplace on file, to replace string """
    subprocess.run(SED + ['-i', 's/' + match + '/' + replacement + '/', file_])


def _sed_remove(file_, match):
    """ Run sed, inplace on file, to replace string """
    subprocess.run(SED + ['-i', '/' + match + '/d', file_])


def _insert(file_, tag, string, after_marker=False):
    """ Add text at marker in file """
    replacement = '%%::' + tag + '::%%\\n' + string if after_marker \
        else string + '\\n%%::' + tag + '::%%'
    _sed_replace(file_, '%%::' + tag + '::%%', replacement)


def _newchapter(name):
    """ Return string for \newchapter """
    return '\\\\newchapter{{{}}}'.format(name)


def init(*argv):
    """ Create a new report """
    argparser = argparse.ArgumentParser()
    argparser.add_argument("name", help="Directory name")
    args = argparser.parse_args(argv)
    assert not _is_inside_report(), "Recursion detected"
    assert not os.path.exists(args.name), "Directory exists, cannot initialize"
    print('Initializing report "{}"'.format(args.name))
    shutil.copytree(INIT_TEMPLATE, args.name)


def add_chapter(*argv):
    """ Add chapter """
    assert _is_inside_report(), "Must be inside report directory"
    argparser = argparse.ArgumentParser()
    argparser.add_argument("names", help="Chapter names", nargs='+')
    argparser.add_argument('--appendix', "-a", help="Insert chapter as appendix",
                           action="store_true")
    args = argparser.parse_args(argv)
    for name in args.names:
        if os.path.exists(name):
            print("Chapter exists: ", name)
            continue
        marker = 'appendices' if args.appendix else "chapters"
        os.makedirs(name)
        with open(os.path.join(CHAPTER_TEMPLATE, 'chapter.tex'), 'r') as input_file:
            with open(os.path.join(name, name + '.tex'), 'w') as output_file:
                output_file.write(input_file.read().format(name=name, capname=name.capitalize()))
        _insert(_indexfile(), marker, '\\\\newchapter{{{}}}'.format(name))
        print("Add appendix" if args.appendix else "Add chapter", name)


def remove_chapter(*argv):
    """ Remove chapter """
    assert _is_inside_report(), "Must be inside report directory"
    argparser = argparse.ArgumentParser()
    argparser.add_argument("name", help="Chapter name")
    args = argparser.parse_args(argv)
    assert os.path.exists(args.name), "Chapter does not exist"
    shutil.rmtree(args.name)
    _sed_remove(_indexfile(), _newchapter(args.name))
    print("Removed chapter ", args.name)


def rename_chapter(*argv):
    """ Rename chapter """
    assert _is_inside_report(), "Must be inside report directory"
    argparser = argparse.ArgumentParser()
    argparser.add_argument("name", help="Chapter name")
    argparser.add_argument("newname", help="New chapter name")
    args = argparser.parse_args(argv)
    assert os.path.exists(args.name), "Chapter does not exist"
    shutil.move(args.name, args.newname)
    _sed_replace(_indexfile(), _newchapter(args.name), _newchapter(args.newname))
    print("Renamed chapter ", args.name, ' -> ', args.newname)


