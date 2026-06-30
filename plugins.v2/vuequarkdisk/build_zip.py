import zipfile, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

exclude_dirs = {'node_modules', '__pycache__', '.git', '.workbuddy'}
exclude_files = {'quarkdisk.zip', 'package.json', 'package-lock.json',
                 'vite.config.js', 'build-zip.js', 'index.html',
                 'Untitled-1.json', 'build_zip.py'}

with zipfile.ZipFile('quarkdisk.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            if f in exclude_files or f.startswith('.'):
                continue
            fp = os.path.join(root, f)
            arcname = fp.replace('\\', '/')
            if arcname.startswith('./'):
                arcname = arcname[2:]
            zf.write(fp, arcname)
    namelist = zf.namelist()
    print(f'Total files: {len(namelist)}')
    for n in sorted(namelist):
        print(f'  {n}')

print(f'Zip size: {os.path.getsize("quarkdisk.zip")} bytes')
