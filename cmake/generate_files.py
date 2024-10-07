from pathlib import Path
import os
import glob
import sys
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
from methods import get_version_info, detect_modules, generated_wrapper
from editor import editor_builders
from editor import template_builders
from editor.icons import editor_icons_builders
from editor.themes import editor_theme_builders
from main import main_builders
# # from misc.scripts import copyright_headers
# from misc.scripts import dotnet_format
# from misc.scripts import file_format
# from misc.scripts import header_guards
import misc.scripts as scripts
from scene.theme import default_theme_builders
from scene.theme.icons import default_theme_icons_builders
from core import core_builders
from core.extension import make_interface_dumper
from core.extension import make_wrappers
import gles3_builders
import glsl_builders
import scu_builders
from core.input import input_builders
from core.object import make_virtuals


def file_to_string(file_path):
    with open(file_path, 'r') as f:
        return f.read()


def dir_contains_cmakelists(dir):

    # check if dir contains CMakeLists.txt
    return os.path.exists(dir / 'CMakeLists.txt')


def version_info_builder(target, version_info):
    with generated_wrapper(target) as file:
        file.write(
            """\
    #define VERSION_SHORT_NAME "{short_name}"
    #define VERSION_NAME "{name}"
    #define VERSION_MAJOR {major}
    #define VERSION_MINOR {minor}
    #define VERSION_PATCH {patch}
    #define VERSION_STATUS "{status}"
    #define VERSION_BUILD "{build}"
    #define VERSION_MODULE_CONFIG "{module_config}"
    #define VERSION_WEBSITE "{website}"
    #define VERSION_DOCS_BRANCH "{docs_branch}"
    #define VERSION_DOCS_URL "https://docs.godotengine.org/en/" VERSION_DOCS_BRANCH
    """.format(**version_info)
        )


def modules_enabled_builder(target, source):
    with generated_wrapper(target) as file:
        for module in source:
            file.write(f"#define MODULE_{module.upper()}_ENABLED\n")
def touch_gentree(gen_dir):
    files = ['/core/object/gdvirtual.gen.inc', 
             '/core/version_generated.gen.h',
            '/modules/modules_enabled.gen.h',
            "/core/extension/ext_wrappers.gen.inc",
            "/core/extension/gdextension_interface_dump.gen.h",
            "/core/extension/gdextension_interface.h",
            '/core/authors.gen.h',
            '/core/donors.gen.h',
            '/core/license.gen.h',
            "/editor/doc_data_compressed.gen.h",
            "/editor/editor_translations.gen.h",
            "/editor/doc_translations.gen.h",
            "/editor/property_translations.gen.h",
            "/editor/extractable_translations.gen.h",
            '/core/io/certs_compressed.gen.h',
            "/scene/theme/default_font.gen.h",
            "/editor/themes/editor_icons.gen.h"]
    #create new file
    for file in files:
        os.makedirs(os.path.dirname(gen_dir + file), exist_ok=True)
        with open(gen_dir + file, 'w') as f:
            f.write("")

if __name__ == '__main__':


    with open(Path(root_dir) / 'core' / 'disabled_classes.gen.h', 'w') as f:
        f.write('#ifndef DISABLED_CLASSES_H\n')
        f.write('#define DISABLED_CLASSES_H\n')
        f.write('#endif\n')
    # run python script "./core/object/make_virtuals.py"

    from core.object import make_virtuals

    gen_dir = str(root_dir / 'build' / 'generated_files') + "/"
    touch_gentree(gen_dir)
    # set root_dir to ./core/object/
    gdvirtual_fname = gen_dir + '/core/object/gdvirtual.gen.inc'
    # create file
    make_virtuals.run([gdvirtual_fname], "", "")

    version_info_builder(
        gen_dir + '/core/version_generated.gen.h', get_version_info())

    modules_detected = detect_modules("modules")

    modules_enabled_builder(
        gen_dir + '/modules/modules_enabled.gen.h', modules_detected)
    make_wrappers.run(["./core/extension/ext_wrappers.gen.inc"], "", "")
    # set working dir to ./core/extension/

    make_interface_dumper.run(["./core/extension/gdextension_interface_dump.gen.h"], [
                              "./core/extension/gdextension_interface.h", "./core/extension/make_interface_dumper.py"], "")

    core_builders.make_authors_header(
        [gen_dir + '/core/authors.gen.h'], [str(root_dir) + "/AUTHORS.md"], "")
    core_builders.make_donors_header(
        [gen_dir + '/core/donors.gen.h'], [str(root_dir) + "/DONORS.md"], "")
    core_builders.make_license_header(
        [gen_dir + '/core/license.gen.h'], [str(root_dir) + "/COPYRIGHT.txt", str(root_dir) + "/LICENSE.txt"], "")
    core_builders.make_certs_header(
        [gen_dir + '/core/io/certs_compressed.gen.h'], [str(root_dir) + "/thirdparty/certs/ca-certificates.crt"], {"system_certs_path": "", "builtin_certs": False})

    # Core API documentation.
    docs = glob.glob(str(root_dir) + "/doc/classes/*.xml")
    # find all *.xml files in ./doc/classes

    docs = sorted(docs)
    editor_builders.make_doc_header(
        ["./editor/doc_data_compressed.gen.h"], docs, "")
    tlist = glob.glob(str(root_dir) + "./editor/translations/editor" + "/*.po")
    editor_builders.make_editor_translations_header(
        ["./editor/editor_translations.gen.h"], tlist, "")

    tlist = glob.glob(str(root_dir) + "./editor/translations/doc" + "/*.po")
    editor_builders.make_doc_translations_header(
        ["./editor/doc_translations.gen.h"], tlist, "")

    tlist = glob.glob(str(root_dir) + "./editor/translations/properties" + "/*.po")
    editor_builders.make_property_translations_header(
        ["./editor/property_translations.gen.h"], tlist, "")

    # extractable
    tlist = glob.glob(str(root_dir) + "./editor/translations/extractable" + "/*.po")
    editor_builders.make_extractable_translations_header(
        ["./editor/extractable_translations.gen.h"], tlist, "")

    #icons
    icon_svgs = glob.glob(str(root_dir) + "/scene/theme/icons/*.svg")
    #replace .svg with .h
    icon_gen_headers = [x.replace(".svg", ".h") for x in icon_svgs]
    [default_theme_icons_builders.make_default_theme_icons_action(hdr, svg) for hdr, svg in zip(icon_gen_headers, icon_svgs, "")]

    editor_icons_builders.make_editor_icons_action([gen_dir + "/editor/themes/editor_icons.gen.h"], icon_svgs, "")

    default_theme_builders.make_fonts_header([gen_dir + "/scene/theme/default_font.gen.h"],
    [str(root_dir) + "//thirdparty/fonts/OpenSans_SemiBold.woff2"], "")


    # # Fonts
    # flist = glob.glob(env.Dir("#thirdparty").abspath + "/fonts/*.ttf")
    # flist.extend(glob.glob(env.Dir("#thirdparty").abspath + "/fonts/*.otf"))
    # flist.extend(glob.glob(env.Dir("#thirdparty").abspath + "/fonts/*.woff"))
    # flist.extend(glob.glob(env.Dir("#thirdparty").abspath + "/fonts/*.woff2"))
    # flist.sort()
    # env.Depends("#editor/themes/builtin_fonts.gen.h", flist)
    # env.CommandNoCache(
    #     "#editor/themes/builtin_fonts.gen.h",
    #     flist,
    #     env.Run(editor_theme_builders.make_fonts_header),
    # )
    font_patterns = ["*.ttf", "*.otf", "*.woff", "*.woff2"]
    fonts = [glob.glob(str(root_dir) + "/thirdparty/fonts/" + pattern) for pattern in font_patterns]
    fonts = [font for sublist in fonts for font in sublist]
    editor_theme_builders.make_fonts_header([gen_dir + "/editor/themes/builtin_fonts.gen.h"], fonts, "")
    # for platform in env.platform_exporters:
    #     for path in glob(f"{platform}/export/*.svg"):
    #         env.CommandNoCache(path.replace(".svg", "_svg.gen.h"), path, env.Run(export_icon_builder))


    # env_main.Depends("#main/splash.gen.h", "#main/splash.png")
    # env_main.CommandNoCache(
    #     "#main/splash.gen.h",
    #     "#main/splash.png",
    #     env.Run(main_builders.make_splash),
    # )

    # if env_main.editor_build and not env_main["no_editor_splash"]:
    #     env_main.Depends("#main/splash_editor.gen.h", "#main/splash_editor.png")
    #     env_main.CommandNoCache(
    #         "#main/splash_editor.gen.h",
    #         "#main/splash_editor.png",
    #         env.Run(main_builders.make_splash_editor),
    #     )

    # env_main.Depends("#main/app_icon.gen.h", "#main/app_icon.png")
    # env_main.CommandNoCache(
    #     "#main/app_icon.gen.h",
    #     "#main/app_icon.png",
    #     env.Run(main_builders.make_app_icon),
    # )

    # env["BUILDERS"]["MakeGDTemplateBuilder"] = Builder(
    #     action=env.Run(build_template_gd.make_templates),
    #     suffix=".h",
    #     src_suffix=".gd",
    # )

    # # Template files
    # templates_sources = Glob("*/*.gd")

    # env.Alias("editor_template_gd", [env.MakeGDTemplateBuilder("templates.gen.h", templates_sources)])
    # env.Alias("editor_template_cs", [env.MakeCSharpTemplateBuilder("templates.gen.h", templates_sources)])
    # if env.editor_build:
    #     env_icu.Depends("#thirdparty/icu4c/icudata.gen.h", "#thirdparty/icu4c/" + icu_data_name)
    #     env_icu.Command("#thirdparty/icu4c/icudata.gen.h", "#thirdparty/icu4c/" + icu_data_name, make_icu_data)
    #     env_text_server_adv.Prepend(CPPPATH=["#thirdparty/icu4c/"])
