# SPDX-License-Identifier: MIT
"""Exercise actual key storage, patched Web API parsers and unchanged login."""
from pathlib import Path
from tempfile import TemporaryDirectory
import io, os, shutil, subprocess, tarfile, unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT/'patches/emulationstation/EmbercadeRetroAchievements.h'
INCLUDE = ROOT.parent/'Batocera-EmulationStation-desktop-test/deps/usr/include'

def compile_probe(root, code):
    source=root/'probe.cpp'; binary=root/'probe'; source.write_text(code)
    result=subprocess.run(['c++','-std=c++17','-I',str(HELPER.parent),'-I',str(INCLUDE),str(source),'-o',str(binary)],capture_output=True,text=True,timeout=45)
    if result.returncode: raise AssertionError(result.stderr)
    return binary

STORAGE = r'''
#include "EmbercadeRetroAchievements.h"
#include <cassert>
using namespace EmbercadeRetroAchievements;
int main(int argc,char**argv) {
 std::string mode=argv[1];
 if(mode=="write") {assert(save("player","synthetic-key&/?"));return 0;}
 if(mode=="read") {assert(keyFor("player")=="synthetic-key&/?");return 0;}
 if(mode=="refuse") {assert(keyFor("player").empty());assert(!save("player","replacement"));assert(!save("player",""));return 0;}
 if(mode=="missing") {assert(keyFor("player").empty());return 0;}
 if(mode=="clear") {assert(save("player",""));assert(keyFor("player").empty());return 0;}
 if(mode=="mismatch") {assert(keyFor("other-player").empty());assert(keyFor("player")=="synthetic-key&/?");return 0;}
 if(mode=="invalid") {
  assert(!save("player",std::string("secret\0hidden",13)));assert(!save("player","bad\nkey"));
  assert(!save("player","bad\rkey"));assert(!save("","key"));assert(!save("player",std::string(2049,'x')));
  assert(keyFor("player")=="synthetic-key&/?");return 0;
 }
 if(mode=="save-fails") {assert(!save("player","replacement"));assert(keyFor("player")=="synthetic-key&/?");return 0;}
 assert(false);
}
'''

class NativeKeyStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('c++'): raise unittest.SkipTest('C++ compiler required')
        cls.temp=TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup)
        cls.binary=compile_probe(Path(cls.temp.name),STORAGE)
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.config=self.root/'config'
        self.folder=self.config/'embercade/secrets';self.file=self.folder/'retroachievements-user.conf'
        self.env={**os.environ,'XDG_CONFIG_HOME':str(self.config)}
    def run_mode(self,mode):
        subprocess.run([str(self.binary),mode],env=self.env,check=True,capture_output=True,timeout=5)
    def test_private_permissions_and_fresh_process_restart(self):
        self.run_mode('write')
        self.assertEqual(self.file.stat().st_mode & 0o777,0o600)
        self.assertEqual(self.folder.stat().st_mode & 0o777,0o700)
        self.run_mode('read')
        self.assertEqual({p.name for p in self.folder.iterdir()},{'retroachievements-user.conf'})
    def test_account_change_does_not_reuse_another_key(self):
        self.run_mode('write');self.run_mode('mismatch')
    def test_clear_only_removes_own_key(self):
        self.run_mode('write');protected=self.folder/'screenscraper-user.conf';protected.write_text('unrelated')
        self.run_mode('clear');self.assertFalse(self.file.exists());self.assertEqual(protected.read_text(),'unrelated')
    def test_missing_key_read_and_clear_create_nothing(self):
        self.run_mode('missing');self.run_mode('clear');self.assertFalse(self.config.exists())
    def test_invalid_fields_preserve_previous_key(self):
        self.run_mode('write');previous=self.file.read_bytes();self.run_mode('invalid');self.assertEqual(previous,self.file.read_bytes())
    def test_unsafe_file_and_directory_permissions_are_not_changed(self):
        for name in ['file','directory']:
            with self.subTest(name=name):
                self.run_mode('write');target=self.file if name=='file' else self.folder
                target.chmod(0o644 if name=='file' else 0o755);previous=self.file.read_bytes();self.run_mode('refuse')
                self.assertEqual(previous,self.file.read_bytes());target.chmod(0o600 if name=='file' else 0o700)
    def test_file_symlink_never_touches_target(self):
        self.run_mode('write');target=self.root/'foreign';target.write_text('unchanged')
        self.file.unlink();self.file.symlink_to(target);self.run_mode('refuse')
        self.assertTrue(self.file.is_symlink());self.assertEqual(target.read_text(),'unchanged')
    def test_secret_directory_symlink_is_refused(self):
        self.run_mode('write');original=self.folder.with_name('original');self.folder.rename(original)
        self.folder.symlink_to(original,target_is_directory=True);self.run_mode('refuse')
    def test_hardlink_is_refused(self):
        self.run_mode('write');os.link(self.file,self.root/'link');self.run_mode('refuse')
    def test_fifo_is_refused_without_blocking(self):
        self.run_mode('write');self.file.unlink();os.mkfifo(self.file,0o600);self.run_mode('refuse')
    def test_malformed_nul_duplicate_and_oversized_files(self):
        self.run_mode('write')
        for content in [b'bad',b'RETROACHIEVEMENTS_WEB_USERNAME=player\n'*2,b'RETROACHIEVEMENTS_WEB_USERNAME=player\nRETROACHIEVEMENTS_WEB_API_KEY=bad\0key\n',b'x'*8193]:
            self.file.write_bytes(content);self.run_mode('missing')
    def test_failed_write_preserves_file_without_temporary_leaks(self):
        self.run_mode('write');self.folder.chmod(0o500);self.addCleanup(self.folder.chmod,0o700)
        self.run_mode('save-fails');self.assertEqual({p.name for p in self.folder.iterdir()},{'retroachievements-user.conf'})

class NativeAchievementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('c++') or not (INCLUDE/'rapidjson/document.h').is_file(): raise unittest.SkipTest('C++ compiler/rapidjson required')
        cls.temp=TemporaryDirectory();cls.addClassCleanup(cls.temp.cleanup);cls.root=Path(cls.temp.name)
        cls.source=cls.root/'frontend';cls.source.mkdir();repo=ROOT.parent/'Batocera-EmulationStation'
        if not (repo/'.git').is_dir(): raise unittest.SkipTest('pinned reference repository required')
        data=subprocess.check_output(['git','-C',str(repo),'archive','1750dded8c0fdff70630026f756a69fcad0bb995'])
        with tarfile.open(fileobj=io.BytesIO(data)) as stream: stream.extractall(cls.source,filter='data')
        for patch in sorted((ROOT/'patches/emulationstation').glob('*.patch')):
            with patch.open('rb') as stream: subprocess.run(['patch','--batch','--forward','-p1','-d',str(cls.source)],stdin=stream,stdout=subprocess.DEVNULL,check=True)
        cls.code=(cls.source/'es-app/src/RetroAchievements.cpp').read_text()
    def test_original_web_api_parsers_user_keys_error_boundaries_and_login(self):
        header=(self.source/'es-app/src/RetroAchievements.h').read_text()
        structs=header[header.index('struct Achievement'):header.index('class RetroAchievements')]
        http=self.code[self.code.index('static HttpReqOptions getHttpOptions()'):self.code.index('std::string GameInfoAndUserProgress::getImageUrl')]
        parser=self.code[self.code.index('int jsonInt('):self.code.index('RetroAchievementInfo RetroAchievements::toRetroAchivementInfo')]
        login=self.code[self.code.index('bool RetroAchievements::testAccount('):]
        klass='''class RetroAchievements {public:
static std::string getApiUrl(const std::string&,const std::string&);
static GameInfoAndUserProgress getGameInfoAndUserProgress(int,const std::string& = "");
static UserSummary getUserSummary(const std::string& = "",int=100);
static UserRankAndScore getUserRankAndScore(const std::string&);
static bool testAccount(const std::string&,const std::string&,std::string&);
};\n'''
        stub=r'''
#include "EmbercadeRetroAchievements.h"
#include <vector>
#include <map>
#include <algorithm>
#include <cassert>
#include <stdexcept>
#include <rapidjson/document.h>
inline std::string _(const char*s){return s;}
namespace Utils {namespace String {inline int toInteger(const std::string&s){return std::stoi(s);}}}
struct HttpReqOptions {std::string userAgent;};
struct HttpReq {
 static std::string body,url;static int code,count;
 HttpReq(const std::string&u,HttpReqOptions*){url=u;count++;}
 static std::string urlEncode(const std::string&s){std::string out;const char*h="0123456789ABCDEF";for(unsigned char c:s){if((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='-'||c=='_')out+=c;else{out+='%';out+=h[c>>4];out+=h[c&15];}}return out;}
 bool wait(){return code==200;}int status(){return code;}
 std::string getContent(){return body;}std::string getErrorMsg(){return "fixed login error";}
};
std::string HttpReq::body,HttpReq::url;int HttpReq::code=200,HttpReq::count=0;
struct SystemConf{static SystemConf*getInstance(){static SystemConf s;return &s;}std::string get(const std::string&){return "key-owner";}};
'''
        main=r'''
int main(){
 auto none=RetroAchievements::getGameInfoAndUserProgress(1);assert(none.ID==0&&!none.Error.empty());
 assert(RetroAchievements::getUserSummary().Username.empty());
 try{RetroAchievements::getUserRankAndScore("key-owner");assert(false);}catch(const std::domain_error&){}
 assert(HttpReq::count==0);
 HttpReq::body=R"({"Success":true,"Token":"normal-emulator-token"})";
 std::string token;assert(RetroAchievements::testAccount("player","password",token));assert(token=="normal-emulator-token");
 assert(HttpReq::url=="https://retroachievements.org/dorequest.php?r=login&u=player&p=password");
 assert(EmbercadeRetroAchievements::save("key-owner","synthetic-web&key/?"));
 HttpReq::body=R"({"ID":1,"Title":"Supported","NumAchievements":1,"NumAwardedToUser":1,"Achievements":{"4":{"ID":4,"Title":"First","Points":5,"DateEarned":"2026-01-01","DisplayOrder":1}}})";
 auto good=RetroAchievements::getGameInfoAndUserProgress(1);
 assert(good.ID==1&&good.Error.empty()&&good.Achievements.size()==1&&good.NumAwardedToUser==1);
 assert(HttpReq::url=="https://retroachievements.org/API/API_GetGameInfoAndUserProgress.php?z=key-owner&y=synthetic-web%26key%2F%3F&u=key-owner&g=1");
 assert(RetroAchievements::getGameInfoAndUserProgress(1,"another-user").ID==1);assert(HttpReq::url.find("&u=another-user&")!=std::string::npos);
 int previous=HttpReq::count;assert(!RetroAchievements::getGameInfoAndUserProgress(0).Error.empty());assert(previous==HttpReq::count);
 for(auto bad:{"{","null","[]",R"({"ID":1,"Title":"Supported","Achievements":42})",R"({"ID":0,"Title":"Unknown"})",R"({"Error":"synthetic-web&key/?"})"}){
  HttpReq::body=bad;auto fail=RetroAchievements::getGameInfoAndUserProgress(1);assert(fail.ID==0&&!fail.Error.empty()&&fail.Error.find("synthetic")==std::string::npos);
 }
 for(auto empty:{"{}","[]"}){HttpReq::body=std::string("{\"ID\":1,\"Title\":\"Empty\",\"Achievements\":")+empty+"}";assert(RetroAchievements::getGameInfoAndUserProgress(1).ID==1);}
 HttpReq::body=R"({"User":"key-owner","TotalPoints":12,"RecentlyPlayed":[{"GameID":1,"Title":"Supported"}],"Awarded":{"1":{"NumAchieved":1}},"RecentAchievements":{"1":{"4":{"ID":4,"Title":"First"}}}})";
 auto summary=RetroAchievements::getUserSummary();assert(summary.Username=="key-owner"&&summary.TotalPoints=="12"&&summary.RecentlyPlayed.size()==1&&summary.Awarded.size()==1&&summary.RecentAchievements.size()==1);
 for(auto bad:{"{","null","[]",R"({"Error":"synthetic-web&key/?"})"}){HttpReq::body=bad;auto fail=RetroAchievements::getUserSummary();assert(fail.Username.empty()&&!fail.Status.empty()&&fail.Status.find("synthetic")==std::string::npos);}
 HttpReq::body=R"({"User":"key-owner","RecentlyPlayed":42,"Awarded":null,"RecentAchievements":{"1":false}})";assert(RetroAchievements::getUserSummary().Username=="key-owner");
 HttpReq::body=R"({"Score":12,"SoftcoreScore":4,"Rank":"2","TotalRanked":10})";assert(RetroAchievements::getUserRankAndScore("key-owner").Score==12);
 for(int code:{401,403,429,500}){HttpReq::code=code;int n=HttpReq::count;auto fail=RetroAchievements::getGameInfoAndUserProgress(1);assert(!fail.Error.empty()&&HttpReq::count==n+1);assert(fail.Error.find("synthetic")==std::string::npos);assert(!RetroAchievements::getUserSummary().Status.empty());}
 assert(EmbercadeRetroAchievements::save("other-player","other-key"));previous=HttpReq::count;
 assert(!RetroAchievements::getGameInfoAndUserProgress(1).Error.empty()&&HttpReq::count==previous);
 assert(EmbercadeRetroAchievements::save("other-player",""));
}
'''
        with TemporaryDirectory() as temp:
            root=Path(temp);binary=compile_probe(root,stub+structs+klass+http+parser+login+main)
            subprocess.run([str(binary)],env={**os.environ,'XDG_CONFIG_HOME':str(root/'config')},check=True,capture_output=True,timeout=10)
    def test_original_login_unchanged_and_key_not_in_generic_settings(self):
        original=subprocess.check_output(['git','-C',str(ROOT.parent/'Batocera-EmulationStation'),'show','1750dded8c0fdff70630026f756a69fcad0bb995:es-app/src/RetroAchievements.cpp'],text=True)
        marker='bool RetroAchievements::testAccount('
        self.assertEqual(self.code[self.code.index(marker):],original[original.index(marker):])
        gui=(self.source/'es-app/src/guis/GuiRetroAchievementsSettings.cpp').read_text()
        self.assertNotIn('addInputTextConfigRow(_("PERSONAL WEB API',gui)
        self.assertIn('EmbercadeRetroAchievements::save(user, key)',gui)
        for name in ('GuiTextEditPopup','GuiTextEditPopupKeyboard'):
            suffix = '.c_str()' if name == 'GuiTextEditPopup' else ''
            self.assertIn(name+'(window, title, value, save, false, _("OK")'+suffix+', true)',gui)
    def test_masked_cache_cursor_and_opt_in_editors(self):
        component=(self.source/'es-core/src/components/TextEditComponent.cpp').read_text()
        methods=component[component.index('void TextEditComponent::onTextChanged()'):component.index('bool TextEditComponent::isMultiline()')]
        for raw in ('wrapText(mText,','buildTextCache(mText,','sizeText(mText.substr','getWrappedTextCursorOffset(mText,'):self.assertNotIn(raw,methods)
        for cls in ('GuiTextEditPopup','GuiTextEditPopupKeyboard'):
            implementation=(self.source/f'es-core/src/guis/{cls}.cpp').read_text()
            self.assertLess(implementation.index('setPassword(password)'),implementation.index('setValue(initValue)'))
            self.assertIn('bool password = false',(self.source/f'es-core/src/guis/{cls}.h').read_text())
        with TemporaryDirectory() as temp:
            root=Path(temp)
            code='#include "EmbercadeRetroAchievements.h"\n#include <cassert>\nint main(){std::string key="synthetic";assert(EmbercadeRetroAchievements::displayText(key,true)==std::string(key.size(),\\\'*\\\'));assert(EmbercadeRetroAchievements::displayText(key,false)==key);}\n'.replace("\\'","'")
            subprocess.run([str(compile_probe(root,code))],check=True,capture_output=True,timeout=5)

    def test_clipboard_batch_paste_preserves_full_value_cursor_and_mask(self):
        source = (self.source/'es-core/src/components/TextEditComponent.cpp').read_text()
        method = source[source.index('bool TextEditComponent::pasteFromClipboard()'):source.index('void TextEditComponent::textInput(')]
        handler = source[source.index('bool TextEditComponent::input('):source.index('void TextEditComponent::update(')]
        stub = r'''
#include "EmbercadeRetroAchievements.h"
#include <cstring>
#include <cassert>
#include <cstdlib>
std::string clipboard;bool available=true,nullResult=false;int reads=0,frees=0;
enum {DEVICE_KEYBOARD=0,SDLK_RETURN=1,SDLK_ESCAPE,SDLK_LEFT,SDLK_RIGHT,SDLK_UP,SDLK_DOWN,SDLK_HOME,SDLK_END,SDLK_DELETE,SDLK_v,SDLK_INSERT,KMOD_CTRL=256,KMOD_SHIFT=512};
const char* BUTTON_OK="ok";
#define CURSOR_REPEAT_START_DELAY 500
#define CURSOR_REPEAT_SPEED 28
int modifiers=0;
int SDL_GetModState(){return modifiers;}
struct Input {int id,value;};
struct InputConfig {int getDeviceId(){return DEVICE_KEYBOARD;}bool isMappedTo(const char*,Input){return false;}bool isMappedLike(const char*,Input){return false;}};
bool SDL_HasClipboardText(){return available;}
char* SDL_GetClipboardText(){reads++;return nullResult?nullptr:strdup(clipboard.c_str());}
void SDL_free(void*p){frees++;free(p);}
struct TextEditComponent {
 std::string mText,visible;unsigned int mCursor=0;bool mPassword=true,multiline=false;
 int mCursorRepeatDir=0,mBlinkTime=0,mCursorRepeatTimer=0;bool mEditing=true,mFocused=true;
 void startEditing(){mEditing=true;}void stopEditing(){mEditing=false;}
 void moveCursor(int n){mCursor+=n;}void setCursor(size_t n){mCursor=n==std::string::npos?mText.size():n;}
 void textInput(const char*){}
 bool input(InputConfig*,Input);
 bool isMultiline(){return multiline;}
 void onTextChanged(){visible=EmbercadeRetroAchievements::displayText(mText,mPassword);}
 void onCursorChanged(){}
 bool pasteFromClipboard();
};
'''
        main = r'''
int main(){
 TextEditComponent shortcut;InputConfig keyboard;clipboard="full-synthetic-shortcut";
 int initial=reads;shortcut.input(&keyboard,{SDLK_v,1});assert(reads==initial&&shortcut.mText.empty());
 modifiers=KMOD_CTRL;shortcut.input(&keyboard,{SDLK_v,0});assert(reads==initial);
 shortcut.input(&keyboard,{SDLK_v,1});assert(shortcut.mText==clipboard&&reads==initial+1);
 modifiers=KMOD_SHIFT;shortcut.input(&keyboard,{SDLK_INSERT,1});assert(shortcut.mText==clipboard+clipboard);
 modifiers=0;
 TextEditComponent field;clipboard=std::string(64,'a')+"-full-synthetic-tail";
 assert(field.pasteFromClipboard());assert(field.mText==clipboard&&field.mCursor==clipboard.size());
 assert(field.visible==std::string(clipboard.size(),'*'));assert(reads==initial+3&&frees==initial+3);
 field.mText="ab";field.mCursor=1;clipboard="synthetic";assert(field.pasteFromClipboard());
 assert(field.mText=="asyntheticb"&&field.mCursor==10);
 field.mText="";field.mCursor=0;clipboard="αβ";assert(field.pasteFromClipboard());assert(field.mText==clipboard&&field.mCursor==clipboard.size());
 auto previous=field.mText;auto cursor=field.mCursor;
 for(auto bad:{"","secret\nkey","secret\rkey","secret\tkey"}){clipboard=bad;assert(!field.pasteFromClipboard());assert(field.mText==previous&&field.mCursor==cursor);}
 clipboard=std::string(16385,'x');assert(!field.pasteFromClipboard());assert(field.mText==previous);
 clipboard=std::string(2049,'x');assert(!field.pasteFromClipboard());assert(field.mText==previous);
 available=false;int n=reads;assert(!field.pasteFromClipboard());assert(reads==n);
 available=true;nullResult=true;assert(!field.pasteFromClipboard());assert(field.mText==previous);
}
'''
        with TemporaryDirectory() as temp:
            root=Path(temp);subprocess.run([str(compile_probe(root,stub+method+handler+main))],check=True,capture_output=True,timeout=5)

    def test_paste_shortcuts_and_buttons_share_native_method(self):
        component=(self.source/'es-core/src/components/TextEditComponent.cpp').read_text()
        self.assertIn('SDLK_v && (SDL_GetModState() & KMOD_CTRL)',component)
        self.assertIn('SDLK_INSERT && (SDL_GetModState() & KMOD_SHIFT)',component)
        for cls in ('GuiTextEditPopup','GuiTextEditPopupKeyboard'):
            code=(self.source/f'es-core/src/guis/{cls}.cpp').read_text()
            self.assertIn('_("PASTE")',code)
            self.assertIn('mText->pasteFromClipboard()',code)
            self.assertIn('Copy the full key again and try Paste.',code)
        keyboard=(self.source/'es-core/src/guis/GuiTextEditPopupKeyboard.cpp').read_text()
        self.assertIn('password ? 2 : 1',keyboard)
        self.assertIn('pasteWidth / mSize.x()',keyboard)
