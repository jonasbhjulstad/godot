from pathlib import Path
import os
import glob
import sys
root_dir = Path(__file__).parent.parent
sys.path.append(root_dir)


def glob_relative_files(directory, pattern, recursive):
    files = glob.glob(directory + pattern, recursive=recursive)
    return [os.path.relpath(file, directory) for file in files]


def glob_headers(directory, recursive):
    return glob_relative_files(directory, "**/*.h", recursive) + glob_relative_files(directory, "**/*.hpp", recursive)


def glob_sources(directory, recursive):
    return glob_relative_files(directory,  "**/*.c", recursive) + glob_relative_files(directory,  "**/*.cpp", recursive)


def add_target(directory, target_name, recursive=True, writemode='w', includes=[], definitions=[], include_pwd = False):
    # pattern to match '.c', '.h', '.hpp', '.cpp', where pp is optional
    source_files = glob_sources(directory, recursive)
    linktype = None
    if source_files:
        linktype = "PUBLIC"
    else:
        linktype = "INTERFACE"

    with open(os.path.join(directory, 'CMakeLists.txt'), writemode) as f:
        f.write('add_library(' + target_name + ' ' + (linktype if linktype == "INTERFACE" else '') + '\n\t'.join(source_files) + ')\n')

        if includes:
            f.write('target_include_directories(' + target_name + ' ' +
                    linktype + ' ' + '\n\t'.join(includes) + ')\n')
        if definitions:
            f.write('target_compile_definitions(' + target_name + ' ' +
                    linktype + ' ' + '\n\t'.join(definitions) + ')\n')
        if include_pwd: 
            f.write('target_include_directories(' + target_name + ' ' +
                    linktype + ' ${CMAKE_CURRENT_SOURCE_DIR' + '})\n')

    return target_name, linktype


def file_append(path, content):
    with open(path, 'a') as f:
        f.write(content)

def get_subtarget_dirs(directory):
    ignore_dirs = ['__pycache__']
    # get the last directory of the 'directory' path
    # only directories
    return [os.path.basename(subdir) for subdir in glob.glob(os.path.join(
        directory, '*')) if (os.path.isdir(subdir) and os.path.basename(subdir) not in ignore_dirs)]

def add_subtargets(directory, include_pwd = False, includes = {}, definitions = {}):
    dirname = os.path.basename(os.path.normpath(directory))
    subdirs = get_subtarget_dirs(directory)
    subtargets = []
    for subdirectory in subdirs:
        if os.path.isdir(os.path.join(directory, subdirectory)):
            subtarget_name = dirname + "_" + subdirectory
            subtargets.append(add_target(
                directory +'/' +  subdirectory + "/", subtarget_name, includes=includes[dirname] + includes[subtarget_name], definitions=definitions[dirname], include_pwd=include_pwd)[0])
    # filter none
    subtargets = list(filter(None, subtargets))
    return subdirs, subtargets


def add_main_targets(directory, includes={}, definitions={}, main_target=True, include_pwd = False):
    main_fname = os.path.join(directory, 'CMakeLists.txt')
    touch_file(main_fname)
    subdirs, subtargets = add_subtargets(directory, includes=includes, definitions=definitions)
    dirname = os.path.basename(os.path.normpath(directory))
    if(main_target):
        _, libtype = add_target(directory, dirname, recursive=False, writemode='w',
                            includes=includes[dirname], definitions=definitions[dirname])
    if subtargets:
        with open(main_fname, 'a') as f:
            [f.write('add_subdirectory(' + s[s.find('_') + 1:] + ')\n')
                for s in subtargets]
            f.write('set(' + dirname + '_SUBTARGETS ' +
                    ' '.join(subtargets) + ')\n')
            if main_target:
                f.write('target_link_libraries(' + dirname + ' ' +
                        libtype + ' ${' + dirname + '_SUBTARGETS})\n')


def touch_file(path):
    with open(path, 'w') as f:
        f.write("")

def generate_cmake_targets():

    parent_targets = ['core', 'drivers', 'editor', 'main',
                      'modules', 'scene', 'servers', 'tests', 'thirdparty', 'platform']
    subdirs = [get_subtarget_dirs(str(root_dir / parent_target)) for parent_target in parent_targets]

    subtargets = [[par + '_' + sub for sub in subdir] for par, subdir in zip(parent_targets, subdirs)]
    #flatten subtargets
    subtargets = [item for sublist in subtargets for item in sublist]
    all_targets = parent_targets + subtargets

    core_dir = str(root_dir) + "/core/"
    gen_dir = str(root_dir) + "/build/generated_files/"

    include_directories = {k: [str(root_dir), gen_dir] if 'thirdparty' not in k else [] for k in all_targets}
    include_directories['thirdparty_clipper2'] = ['${CMAKE_CURRENT_LIST_DIR' + '}/include/']

    definitions = {k: ['ENABLE_DEBUG', 'DEBUG_ENABLED', 'TOOLS_ENABLED'] if 'thirdparty' not in k else [] for k in all_targets}
    
    definitions['thirdparty'] = []
    

    for parent_target in parent_targets:
        parent_dir = str(root_dir / parent_target) + "/"
        if parent_target != 'thirdparty':
            add_main_targets(parent_dir, include_directories, definitions)
    
    add_main_targets(str(root_dir / 'thirdparty/'), include_pwd=True, includes=include_directories, definitions=definitions, main_target=False)
if __name__ == '__main__':
    generate_cmake_targets()
