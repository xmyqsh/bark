cc_library(
    name = "spdlog",
    srcs = glob(["src/*.cpp"]),
    hdrs = glob(["include/**/*.h"]),
    defines = ["SPDLOG_COMPILED_LIB"],
    includes = ["include"],
    linkopts = ["-pthread"],
    visibility = ["//visibility:public"],
)
