import unittest,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from social_links import tracking_url,social_copy
class SocialLinks(unittest.TestCase):
 def test_distinct_channels(self):
  for channel in ['x','telegram']:
   url=tracking_url('https://therwawire.com/news/example/',channel,'2026-10-07-example')
   self.assertIn('utm_source='+channel,url);self.assertIn('utm_medium=social',url)
 def test_no_duplicate_links(self):
  url='https://therwawire.com/learn/example/'
  once=social_copy('Guide\n'+url,url,'x','guide')
  self.assertEqual(once,social_copy(once,url,'x','guide'))
 def test_caption_limit_preserves_destination(self):
  text=social_copy('Long story '*200,'https://therwawire.com/news/example/','telegram','news',1024)
  self.assertLessEqual(len(text),1024);self.assertTrue(text.endswith('utm_campaign=news'));self.assertEqual(text.count('https://'),1)
 def test_rejects_foreign_destinations(self):
  for url in ['https://evil.test/news/example/','https://therwawire.com@evil.test/','http://therwawire.com/']:
   with self.assertRaises(ValueError):tracking_url(url,'x','test')
 def test_removes_unrelated_query_and_fragment(self):
  url=tracking_url('https://therwawire.com/news/example/?email=private#confirm=secret','x','test')
  self.assertNotIn('private',url);self.assertNotIn('secret',url)

class ChannelPause(unittest.TestCase):
 def test_paused_x_needs_no_credentials_and_makes_no_request(self):
  import subprocess,os,tempfile
  root=pathlib.Path(__file__).resolve().parents[1]
  with tempfile.NamedTemporaryFile() as tmp:
   env={k:v for k,v in os.environ.items() if not k.startswith('X_')};env['GITHUB_ENV']=tmp.name
   result=subprocess.run([sys.executable,str(root/'scripts/x_publish.py'),'publish/distribution/no-send.json'],cwd=root,env=env,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr);self.assertIn('paused',result.stdout)
   self.assertIn('X_BLOCKED=true',pathlib.Path(tmp.name).read_text())
 def test_partial_publication_markers_persist_after_x_failure(self):
  root=pathlib.Path(__file__).resolve().parents[1]
  for name in ['market-pulse','evergreen-social']:
   persist=(root/'.github/workflows'/f'{name}.yml').read_text().split('      - name: Persist publication markers')[1]
   self.assertIn('always()',persist);self.assertIn('git diff --cached --quiet',persist)
