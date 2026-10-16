"""Create a deterministic private source ZIP from committed project files.
Requires git for file enumeration. Excludes local state, caches and dependencies.
The manifest provides accidental-corruption checks, not authenticity.
"""
import argparse,hashlib,json,subprocess,zipfile,stat
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent
DENIED={'.git','.state','node_modules','__pycache__','shots'}

def allowed(name):
    path=PurePosixPath(name)
    return (bool(name) and '\\' not in name and ':' not in name and not path.is_absolute() and '..' not in path.parts and
            not set(path.parts)&DENIED and path.name not in ('server.pid','server.log') and
            path.suffix not in ('.log','.pyc'))

def build(output,root=ROOT):
    names=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    payload={}
    for name in sorted(names):
        if not name or not allowed(name):continue
        source=root/name
        if source.is_symlink() or not source.is_file():raise ValueError('source must be a regular project file')
        if not source.resolve().is_relative_to(root.resolve()):raise ValueError('source leaves project directory')
        payload[name]=source.read_bytes()
    manifest={'schema':'veil-source-manifest-v1','scope':'private project source; no local session state',
              'files':{name:hashlib.sha256(data).hexdigest() for name,data in payload.items()}}
    payload['SOURCE-MANIFEST.json']=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,data in sorted(payload.items()):
            entry=zipfile.ZipInfo('veil/'+name,date_time=(2026,1,1,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o100644<<16
            archive.writestr(entry,data,compresslevel=9)
    return {'files':len(payload),'sha256':hashlib.sha256(Path(output).read_bytes()).hexdigest()}

def verify(path):
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if len(names)>256 or sum(i.file_size for i in archive.infolist())>16000000:raise ValueError('package exceeds supported size')
        if any(stat.S_ISLNK(i.external_attr>>16) for i in archive.infolist()):raise ValueError('package symlink rejected')
        if len(set(names))!=len(names) or any(not n.startswith('veil/') or not allowed(n) for n in names):
            raise ValueError('invalid package paths')
        manifest=json.loads(archive.read('veil/SOURCE-MANIFEST.json'))
        if not isinstance(manifest,dict):raise ValueError('invalid source manifest')
        if manifest.get('schema')!='veil-source-manifest-v1' or not isinstance(manifest.get('files'),dict):
            raise ValueError('invalid source manifest')
        if any(not isinstance(n,str) or not allowed(n) or not isinstance(h,str) or len(h)!=64 for n,h in manifest['files'].items()):raise ValueError('invalid source manifest entries')
        expected={'veil/'+n for n in manifest['files']}|{'veil/SOURCE-MANIFEST.json'}
        if set(names)!=expected:raise ValueError('source manifest coverage mismatch')
        for name,digest in manifest['files'].items():
            if hashlib.sha256(archive.read('veil/'+name)).hexdigest()!=digest:raise ValueError('source hash mismatch')
    return {'verified_files':len(names),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('zip_path');p.add_argument('--verify',action='store_true');args=p.parse_args()
    print(json.dumps(verify(args.zip_path) if args.verify else build(args.zip_path),indent=2))
