import re, shutil

def strip_types(src: str) -> str:
    # Remove interfaces, type aliases, enums -> const object, annotations (conservative regexes).
    src = re.sub(r'(?ms)^\s*interface\s+\w+[^{]*\{[^}]*\}\s*', '', src)
    src = re.sub(r'(?m)^\s*type\s+\w+[^=]*=[^;]+;\s*', '', src)
    # enum X { A, B } -> const X = { A: 0, B: 1 };
    def _enum(m):
        name, body = m.group(1), m.group(2)
        items = [x.strip().split('=')[0].strip() for x in body.split(',') if x.strip()]
        return 'const %s = { %s };' % (name, ', '.join('%s: %d' % (k, i) for i, k in enumerate(items)))
    src = re.sub(r'enum\s+(\w+)\s*\{([^}]*)\}', _enum, src)
    src = re.sub(r':\s*(?:string|number|boolean|void|any|unknown|never|bigint|symbol|object|[A-Z]\w*(?:\[\])?)(?=[\s,)=;{\n])', '', src)
    src = re.sub(r'<[A-Za-z_][\w\s,\[\]\.|<>]*>\s*\(', '(', src)
    src = re.sub(r'\bas\s+\w+(\[\])?', '', src)
    src = re.sub(r'(?m)^\s*import\s+type\s+.*$', '', src)
    return src

def tsc_available() -> bool:
    return shutil.which('tsc') is not None or shutil.which('npx') is not None
