import json,tempfile,unittest,zipfile
from unittest.mock import patch
from pathlib import Path
from package_lab import allowed,build,verify
class PackageTests(unittest.TestCase):
    def test_sensitive_and_unsafe_paths_excluded(self):
        for name in ('.state/dialog.json','node_modules/x.js','../escape','/absolute','.git/config','shots/image.png','server.pid','run.log','C:/escape','folder\\escape'):
            self.assertFalse(allowed(name),name)
        self.assertTrue(allowed('examples/demo.json'))
    def test_deterministic_package_and_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'code.py').write_text('print(1)\n');(root/'.state').mkdir();(root/'.state/session.json').write_text('private')

            first=root/'a.zip';second=root/'b.zip'
            with patch('package_lab.subprocess.check_output',return_value=b'code.py\0.state/session.json\0'):
                self.assertEqual(build(first,root),build(second,root))
            self.assertEqual(verify(first)['verified_files'],2)
            with zipfile.ZipFile(first) as z:self.assertNotIn('veil/.state/session.json',z.namelist())
    def test_mutated_payload_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.zip'
            with zipfile.ZipFile(path,'w') as z:
                z.writestr('veil/a.py','bad');z.writestr('veil/SOURCE-MANIFEST.json',json.dumps({'schema':'veil-source-manifest-v1','files':{'a.py':'0'*64}}))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):verify(path)
    def test_symlink_source_cannot_copy_external_contents(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'secret').write_text('not source')
            (root/'link.py').symlink_to(root/'secret')
            with patch('package_lab.subprocess.check_output',return_value=b'link.py\0'):
                with self.assertRaisesRegex(ValueError,'regular'):build(root/'output.zip',root)
    def test_archive_symlink_rejected_before_reading_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.zip'
            entry=zipfile.ZipInfo('veil/link');entry.external_attr=0o120777<<16
            with zipfile.ZipFile(path,'w') as z:z.writestr(entry,'/outside')
            with self.assertRaisesRegex(ValueError,'symlink'):verify(path)
    def test_invalid_manifest_root_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bad.zip'
            with zipfile.ZipFile(path,'w') as z:z.writestr('veil/SOURCE-MANIFEST.json','null')
            with self.assertRaisesRegex(ValueError,'manifest'):verify(path)
if __name__=='__main__':unittest.main(verbosity=2)
