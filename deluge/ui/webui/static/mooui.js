
Usage: java -jar yuicompressor-x.y.z.jar [options] [input file]

Global Options
  -h, --help                Displays this information
  --type <js|css>           Specifies the type of the input file
  --charset <charset>       Read the input file using <charset>
  --line-break <column>     Insert a line break after the specified column number
  -v, --verbose             Display informational messages and warnings
  -o <file>                 Place the output into <file>. Defaults to stdout.

JavaScript Options
  --nomunge                 Minify only, do not obfuscate
  --preserve-semi           Preserve all semicolons
  --disable-optimizations   Disable all micro optimizations

If no input file is specified, it defaults to stdin. In this case, the 'type'
option is required. Otherwise, the 'type' option is required only if the input
file extension is neither 'js' nor 'css'.
