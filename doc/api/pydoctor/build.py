"""
Pydoctor API Runner
---------------------

Using pkg_resources, we attempt to see if pydoctor is installed,
if so, we use its cli program to compile the documents
"""
try:
    import sys
    import os
    import shutil
    import pkg_resources
    pkg_resources.require("pydoctor")

    from pydoctor.driver import main
    sys.argv = '''pydoctor.py --quiet
        --project-name=Pymodbus3
        --project-url=http://uzumaxy.github.io/pymodbus3/
        --add-package=../../../pymodbus3
        --html-output=html
        --html-write-function-pages --make-html'''.split()

    print("Building Pydoctor API Documentation")
    main(sys.argv[1:])

    if os.path.exists('../../../build'):
        shutil.move("html", "../../../build/pydoctor")
except:
    print("Pydoctor unavailable...not building")
