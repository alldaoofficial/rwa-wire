import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const script=fs.readFileSync(new URL('../src/components/GrowthAnalytics.astro',import.meta.url),'utf8').split('<script is:inline define:vars={{ endpoint }}>')[1].split('</script>')[0];
function load(search,path='/news/example/'){const payloads=[];const win={};vm.runInNewContext(script,{endpoint:'https://example.test',location:{pathname:path,search},document:{referrer:'https://t.co/abc',addEventListener(){}},window:win,URL,URLSearchParams,fetch:async(url,opts)=>{payloads.push(JSON.parse(opts.body));}});return {payloads,win};}
test('marked arrivals carry only channel and campaign; actions retain attribution',()=>{for(const source of ['x','telegram']){const {payloads,win}=load(`?utm_source=${source}&utm_medium=social&utm_campaign=article-1&email=private#secret`);assert.equal(payloads[0].event,'social_landing');assert.deepEqual(payloads[0].metadata,{source,campaign:'article-1'});assert.equal(payloads[0].path,'/news/example/');win.rwaAnalytics.track('newsletter_submit','newsletter',{placement:'article-newsletter'});assert.equal(payloads[1].metadata.source,source);assert.ok(!JSON.stringify(payloads).includes('private'));}});
test('ordinary, unknown and malformed links do not generate social arrivals',()=>{for(const q of ['', '?utm_source=evil&utm_medium=social&utm_campaign=x','?utm_source=x&utm_medium=email&utm_campaign=x','?utm_source=x&utm_medium=social&utm_campaign=%3Cscript%3E'])assert.equal(load(q).payloads.length,0);});
test('admin pages do not generate acquisition arrivals',()=>{assert.equal(load('?utm_source=x&utm_medium=social&utm_campaign=test','/analytics/').payloads.length,0);});
