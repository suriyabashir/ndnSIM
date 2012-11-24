## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-

import os
import Logs
import Utils
import Options

from waflib.Errors import WafError

import wutils

def options(opt):
    opt.tool_options('boost', tooldir=["waf-tools"])
    opt.add_option('--enable-ndn-plugins',
                   help=("Enable NDN plugins (may require patching).  topology plugin enabled by default"),
                   dest='enable_ndn_plugins')

    opt.add_option('--disable-ndn-plugins',
                   help=("Enable NDN plugins (may require patching).  topology plugin enabled by default"),
                   dest='disable_ndn_plugins')

def configure(conf):
    try:
        conf.check_tool('boost')
        conf.check_boost(lib = 'iostreams')
    except WafError:
        conf.env['LIB_BOOST'] = []

    conf.env['ENABLE_NDNSIM']=False;

    if not conf.env['LIB_BOOST']:
        conf.report_optional_feature("ndnSIM", "ndnSIM", False,
                                     "Required boost libraries not found")
        conf.env['MODULES_NOT_BUILT'].append('ndnSIM')
        return
    else:
        boost_version = conf.env.BOOST_VERSION.split('_')
        if int(boost_version[0]) < 1 or int(boost_version[1]) < 48:
            conf.report_optional_feature("ndnSIM", "ndnSIM", False,
                                         "ndnSIM requires at least boost version 1.48")
            conf.env['MODULES_NOT_BUILT'].append('ndnSIM')

            Logs.error ("ndnSIM requires at least boost version 1.48")
            Logs.error ("Please upgrade your distribution or install custom boost libraries (http://ndnsim.net/faq.html#boost-libraries)")
            return

    conf.env['NDN_plugins'] = ['topology']
    if Options.options.enable_ndn_plugins:
        conf.env['NDN_plugins'] = conf.env['NDN_plugins'] + Options.options.enable_ndn_plugins.split(',')

    if Options.options.disable_ndn_plugins:
        conf.env['NDN_plugins'] = conf.env['NDN_plugins'] - Options.options.disable_ndn_plugins.split(',')
    
    conf.env['ENABLE_NDNSIM']=True;
    conf.env['MODULES_BUILT'].append('ndnSIM')

    conf.report_optional_feature("ndnSIM", "ndnSIM", True, "")

def build(bld):
    deps = ['core', 'network', 'point-to-point']
    deps.append ('internet') # Until RttEstimator is moved to network module
    if bld.env['ENABLE_PYTHON_BINDINGS']:
        deps.append ('visualizer')

    if 'topology' in bld.env['NDN_plugins']:
        deps.append ('topology-read')

    if 'mobility' in bld.env['NDN_plugins']:
        deps.append ('mobility')

    module = bld.create_ns3_module ('ndnSIM', deps)
    module.uselib = 'BOOST BOOST_IOSTREAMS'

    headers = bld.new_task_gen(features=['ns3header'])
    headers.module = 'ndnSIM'

    if not bld.env['ENABLE_NDNSIM']:
        bld.env['MODULES_NOT_BUILT'].append('ndnSIM')
        return
   
    module.source = bld.path.ant_glob(['model/**/*.cc',
                                       'apps/*.cc',
                                       'utils/**/*.cc',
                                       'helper/**/*.cc',
                                       ])

    headers.source = [
        "helper/ndn-stack-helper.h",
        "helper/ndn-app-helper.h",
        "helper/ndn-header-helper.h",
        "helper/ndn-face-container.h",
        "helper/ndn-global-routing-helper.h",

        "apps/ndn-app.h",

        "model/ndn-l3-protocol.h",
        "model/ndn-face.h",
        "model/ndn-app-face.h",
        "model/ndn-net-device-face.h",
        "model/ndn-interest.h",
        "model/ndn-content-object.h",
        "model/ndn-name-components.h",

        "model/cs/ndn-content-store.h",

        "model/fib/ndn-fib.h",
        "model/fib/ndn-fib-entry.h",
        
        "model/pit/ndn-pit.h",
        "model/pit/ndn-pit-entry.h",
        "model/pit/ndn-pit-entry-incoming-face.h",
        "model/pit/ndn-pit-entry-outgoing-face.h",
        
        "model/fw/ndn-forwarding-strategy.h",
        "model/fw/ndn-fw-tag.h",

        # "utils/batches.h",
        "utils/ndn-limits.h",
        # "utils/weights-path-stretch-tag.h",

        ]

    if 'topology' in bld.env['NDN_plugins']:
        headers.source.extend ([
            "plugins/topology/rocketfuel-weights-reader.h",
            "plugins/topology/annotated-topology-reader.h",
            ])
        module.source.extend (bld.path.ant_glob(['plugins/topology/*.cc']))

    if 'mobility' in bld.env['NDN_plugins']:
        headers.source.extend ([
            "plugins/mobility/spring-mobility-model.h",
            "plugins/mobility/spring-mobility-helper.h",
            ])
        module.source.extend (bld.path.ant_glob(['plugins/mobility/*.cc']))

    ndnSIM_headers = [p.path_from(bld.path) for p in bld.path.ant_glob([
                'utils/**/*.h',
                'model/**/*.h',
                'apps/**/*.h',
                'helper/**/*.h',
                ])]
    bld.install_files('${INCLUDEDIR}/%s%s/ns3/ndnSIM' % (wutils.APPNAME, wutils.VERSION), ndnSIM_headers, relative_trick=True)
    # bld.install_files('$PREFIX/include', ndnSIM_headers)
    
    tests = bld.create_ns3_module_test_library('ndnSIM')
    tests.source = bld.path.ant_glob('test/*.cc')

    if bld.env.ENABLE_EXAMPLES:
        bld.add_subdirs('examples')

    bld.ns3_python_bindings()
