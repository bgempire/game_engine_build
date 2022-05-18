#The MIT License (MIT)
#
#Copyright (c) 2015 Robert Planas Jimenez
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

#NOTE FROM THE AUTHOR:
# Your game is not a "substantial portion" of the Software.
# The Simple Launcher is Public Domain
# Blenderplayer is GPL 3, if you are going to use it, copy its License file.
# Don't worry too much about how easily your game can be modified, the better
# games are those who have mods and thousands of pirated copies.

import bpy
from bpy.props import *

import shutil, re
import os, sys, stat
import platform as libplatform

import threading

import urllib.request
import zipfile

bl_info = {
    "name": "Build Game",
    "author": "Robert Planas (elmeunick9)",
    "location": "Render Properties > Build Game // Platforms // Tools",
    "category": "Game Engine",
    "wiki_url": "http://blenderartists.org/forum/showthread.php?340504-New-BGE-Addon-%28Build-Game%29",
    "blender": (2, 73, 0),
    "description": "Make your game ready for share in multiple platforms."
}

############################ GLOBALS ################################
class BuildGameAddon:
    version = 150205        #Version of the addon, change only when there are important changes.
    project_root = ""       #Root directory of the project, none for nodir, ex: "../../"
    player_root = "engine/" #Root of the player

############################ UTILS ##################################

def is_default_player (os_t, arch, player):
    
    if libplatform.system() == 'Linux': default_os = 'lin'
    if libplatform.system() == 'Windows': default_os = 'win'
    if libplatform.system() == 'Mac': default_os = 'mac'
    
    narch = bpy.app.build_platform.decode("utf-8")
    narch = narch[narch.find(':')+1:narch.rfind('bit')]
    default_arch = 'x' + narch
    
    if os_t == default_os and arch == default_arch and player == 'blenderplayer': return True
    else: return False 


def get_magic_paths(platform):
    magic_path = platform.type_build
    if not magic_path == 'custom':
        magic_path = magic_path + platform.default_architecture[1:]
        magic_path = bpy.utils.user_resource('DATAFILES', 'platform' + os.sep + magic_path, True) + os.sep
        player = magic_path + platform.default_player + os.sep
        launcher = magic_path + platform.default_launcher + os.sep 
    else:
        player = bpy.path.abspath(platform.custom_player_path)
        launcher = bpy.path.abspath(platform.custom_launcher_path)
        playerd = ""; launcherd = ""
        if os.path.isdir(player): playerd = os.sep
        if os.path.isdir(launcher): launcherd = os.sep
        player = os.path.abspath(player) + playerd
        launcher = os.path.abspath(launcher) + launcherd
        
        
    return [magic_path, player, launcher]

def new_install(version_filepath): #Of the addon, not blender
    #Delete old data
    platform_folder = os.path.dirname(version_filepath) + os.sep + "platform"
    try:
        shutil.rmtree(platform_folder)
    except: pass
    
    #Update the version file
    file = open(version_filepath, "w")
    file.write(str(BuildGameAddon.version))
    file.close()

    #Install simple_launcher.zip
    try:
        addon_folder = bpy.utils.user_resource('SCRIPTS', 'addons' + os.sep + 'game_engine_build' + os.sep)
        filepath = addon_folder + 'simple_launcher.zip'
        
        zip = zipfile.ZipFile(filepath)
        zip.extractall(platform_folder)
        zip.close()

    except Exception as ex:
        print(ex)
        return

    #Greets the user
    print("BUILD GAME ADDON: Hello, I've been installed!")
    print("Check how to use me on my thread --> http://blenderartists.org/forum/showthread.php?340504-Build-Game-Addon")

def check_new_install():
    verfile = bpy.utils.user_resource('DATAFILES') + "build_game_addon_version.txt"
    
    if(os.path.isfile(verfile)):
        file = open(verfile, "r")
        file_version = file.read()
        if(file_version != str(BuildGameAddon.version)):
            print("BUILD GAME #001: Versions don't match, I'll proced to reinstall myself.")
            new_install(verfile)
       
    else:
        new_install(verfile)

def in_any (elements, iterable):
    for i in elements:
        if i in iterable:
            return True
    return False
    

###################################### EVENTS ######################################### 


# Check if the current configuration need to be installed or not.
# Disable/Enable Active and Overwrite buttons if it's nesscesary.
def active_click (self, context):
    if RENDER_PT_Platforms.enabled == True: self.user_active = self.active

    
def check_add (self, context):
    bs = context.scene.ge_build_settings
    bs.platforms_active = len(bs.platforms)-1
    platform = bs.platforms[bs.platforms_active]
    
    RENDER_PT_Platforms.enabled = True
    
    check(platform, context)


# Update from: check_add, platforms_active, type_build, architecture, default_player, default_launcher.
def check(self, context):
    bs = context.scene.ge_build_settings
    platform = bs.platforms[bs.platforms_active]
    
    magic_path, player, launcher = get_magic_paths(platform)
  
    # Check if installed
    if os.path.exists(player): player_exist = True        
    else: player_exist = os.path.isdir(player)
        
    if os.path.exists(launcher): launcher_exist = True        
    else: launcher_exist = os.path.isdir(launcher)
    
    installed = (player_exist and launcher_exist and not DownloadPlatformResource.thread.isAlive())
    RENDER_PT_Platforms.player_exist = player_exist
    RENDER_PT_Platforms.launcher_exist = launcher_exist
      
    # Check for included blenderplayer
    if is_default_player(platform.type_build, platform.default_architecture, platform.default_player):
        if not magic_path == 'custom':
            if launcher_exist: installed = True
            if platform.build_merge: installed = True
            RENDER_PT_Platforms.player_exist = True
                
    # Update interface
    if installed:
         if not RENDER_PT_Platforms.enabled: platform.active = platform.user_active
         else: platform.user_active = platform.active
    else:
        if RENDER_PT_Platforms.enabled: platform.user_active = platform.active
        RENDER_PT_Platforms.enabled = False #Quick hack
        platform.active = False

    RENDER_PT_Platforms.enabled = installed

    # Update platform.name for standard configurations
    platformX = {"Linux_32bit", "Linux_64bit", "Windows_32bit", "Windows_64bit",
                 "Mac_32bit", "Mac_64bit", "PlatformX"}
    if platform.name in platformX:
        name = "PlatformX"
        if   platform.type_build == "lin": name = "Linux_"
        elif platform.type_build == "win": name = "Windows_"
        elif platform.type_build == "mac": name = "Mac_"
        if name != "PlatformX": name += platform.default_architecture[1:] + "bit"
        platform.name = name

    #Check and update BuildGameAddon.project_root if nescesary
    name = bpy.path.basename(bpy.data.filepath).replace('.blend','')
    source_name = bpy.path.abspath('//')
    source_name = source_name[:len(source_name)-1]
    source_name = bpy.path.basename(source_name)

    if source_name and (name == source_name or name == bs.game_name):
        BuildGameAddon.project_root = "./"



##################################### BUILD GAME RUTINE #########################################
#TODO: Once the addon is splited in files, use the SuperCopy class also in the download class.
import time

class SuperCopy ():
    
    def __init__ (self, ref):
        self.stop = False
        self.ref = ref
        self.progress = 0
        self.overwritte = False
        self.size = 0
    
    
    def update_progress(self, progress, state):
        if progress >= 1: progress = 1
        if progress <= 0: progress = 0
        state = state + ' ' * (28 - len(state))
        print(state + '[{0:39s}] {1:.1f}%'.format('=' * int(progress * 39), int(progress*100)), end = '\r')
        
        
    def copyFile (self, source, dest_file, max, message):
        # Copy only one file, update the "max" whiletime.
        # Open src and dest files, get src file size
        
        min = self.progress
        
        if not self.overwritte:
            if os.path.isfile(dest_file): return
        
        if not os.path.exists(os.path.dirname(dest_file)):
            os.makedirs(os.path.dirname(dest_file))
        
        src = open(source, "rb")
        dest = open(dest_file, "wb")
        
        src_size = os.stat(source).st_size
        
        block_size = 16384
        cur_block_pos = 0
        while True:
            if self.stop: raise Exception ("Building stoped by the user.")
            
            cur_block = src.read(block_size)
            
            if not cur_block:
                break
            else:
                cur_block_pos += block_size
                dest.write(cur_block)
                
                if cur_block_pos/block_size >= 1:
                    self.update_progress(min + max/100, message)
                else: 
                    self.update_progress(min + (cur_block_pos/src_size)*(max/100), message)
                  
        src.close()
        dest.close()
        
        # Check output file is same size as input one!
        dest_size = os.stat(dest_file).st_size
        if dest_size != src_size:
            raise IOError(
                "New file-size does not match original (src: %s, dest: %s)" % (
                src_size, dest_size)
            )

                
    def copy(self, source, max, subject, dest="", exclude=[]):
        # Check for overwritte
        # Update the progress bar, where max is the maxium progress.
        
        if not dest: dest = self.ref.game_directory
        plat = "(" + str(self.ref.platform_index) + "/" + str(len(self.ref.platform_list)) + ") "
        
        # Check if source is a file and exist
        if os.path.isfile(source):
            self.copyFile(source, dest + os.path.basename(source), max, plat + "Coping " + subject + "...")
            
        else:
            if os.path.isdir(source):
                
                #Check the total size to copy, recusively, only one time/platform.
                if not self.size:
                    for root, dirs, files in os.walk(source):
                        for file in files:
                            self.size += os.stat(os.path.join(root, file)).st_size
                            
                
                dirlist = os.listdir(source)
                
                # If it's an empty directory, make an empty one.
                if dirlist == []:
                    try:
                        os.makedirs(dest)
                        return
                    except FileExistsError: return
                
                # If it has contents, check the size and copy.
                for name in dirlist:
                    if os.path.isfile(source + name):
                        filesize = os.stat(source + name).st_size
                        
                        self.progress = self.progress + (filesize/self.size) * (max/100)
                        
                        if source+name not in exclude:
                            self.copyFile(
                                source + name, dest + name,
                                self.progress,
                                plat + "Coping " + subject + "...")
                                
                        
                    else:
                        if source+name not in exclude:
                            self.copy(source + name + os.sep, max, subject, dest + name + os.sep)
            
                
            else:
                print("BUILD GAME #002: (" + subject + ") File or directory not found")
                print(source)

       

class PlatformInstall(threading.Thread):
    game_name = "Unknow"
    game_directory = "//lib/"
    context = None
    status = ""
    overwritte = True
    
    
    def run(self):
        
        bs = self.context.scene.ge_build_settings
        
        self.status = "Working, look in the console for now..."
        self.size = 0
        self.scp = SuperCopy(self)
        self.scp.overwritte = self.overwritte
        
        #Check for startup blend
        #Warning, doing ops in this thread crashes blender.
        #So, this is done on the buid operator.
        #if not bpy.data.filepath:
        #    bpy.ops.wm.save_mainfile()

        print("------------ BUILD GAME ------------")
        
        self.platform_list = []
        for platform in bs.platforms:
            if platform.active == False: continue
            self.platform_list.append(platform)
        
        self.platform_index = 0
        for platform in self.platform_list:
            self.scp.progress = 0.00
            self.platform_index += 1
            
            try: self.install(platform)
            except:
                print()
                print("Stop.")
                break
            
        self.status = ""
        del self.scp
        print("------------------------------------")
        
        
    def install(self, platform):
            bs = self.context.scene.ge_build_settings
        
            magic_path, player_path, launcher_path = get_magic_paths(platform)
            self.overwritte = platform.overwritte
            dest = self.game_directory + platform.name + os.sep

            # Install PLAYER
            if is_default_player(platform.type_build, platform.default_architecture, platform.default_player):
                self.copyDefaultPlayer(dest + BuildGameAddon.player_root)
            
            else:
                self.scp.copy(player_path, 50, "player", dest + BuildGameAddon.player_root)
            
            # Install LAUNCHER
            if platform.build_merge:
                print("WARNING: Merge is strongly discoraged. See the details form:")
                print("http://blenderartists.org/forum/showthread.php?259752-The-GPL-Answer-Thread")
                print()
                print("Not even implemented yet!")
                
            else:
                self.scp.copy(launcher_path, 70, "launcher", dest)
            
            
            #Install SOURCE
            name = bpy.path.basename(bpy.data.filepath).replace('.blend','')
            source = bpy.data.filepath
            
            source_name = bpy.path.abspath('//')
            source_name = source_name[:len(source_name)-1]
            source_name = bpy.path.basename(source_name)
            
            source_dir = bpy.path.abspath("//" + BuildGameAddon.project_root)
            source_dir = os.path.abspath(source_dir) + os.sep

            if BuildGameAddon.project_root:  
                self.scp.copy(source_dir, 95, "your directory", dest)
            else:
                self.scp.copy(source, 95, "your file", dest)
            
            print(source)
            print("Dir: " + source_dir)

            #Configure SOURCE
            import runpy
            filelist = os.listdir(dest)
            for file in filelist:
                if file == '__launcher__.py' \
                or file == '__player__.py':
                    try:
                        runpy.run_path(dest + file, init_globals = {
                            'blend': source[len(source_dir):],
                            'player': BuildGameAddon.player_root + platform.default_player,
                            'launcher': platform.default_launcher,
                            'arch': platform.default_architecture,
                            'game': bs.game_name,
                            '__file__': dest + file,
                            '__path__': dest,
                            }, run_name='__main__')
                    except Exception as e:
                        print(e)
                        
                    os.remove(dest + file)
            
            
            self.scp.update_progress(1, platform.name)
            print() #New Line, end of progress bar.
            
            
    def stopMe(self):
        self.scp.stop = True                
        
        
    def copyDefaultPlayer(self, dest):
        ext = ''
        platform = self.platform_list[self.platform_index-1]
        if platform.type_build == 'win': ext = '.exe'
        
        player = os.path.join(os.path.dirname(bpy.app.binary_path), "blenderplayer" + ext)
        
        #Welcome to: Find the Python lib quest!
        blender_version = str(bpy.app.version[0]) + '.' + str(bpy.app.version[1])
        python_version = 'python' + str(sys.version_info[0]) + '.' + str(sys.version_info[1])
        
        pylib_root = os.path.join(os.path.dirname(bpy.app.binary_path), blender_version) + os.sep
        if platform.default_architecture == 'lin':
            test = 'python' + os.sep + 'lib' + os.sep + python_version + os.sep
        else:
            test = 'python' + os.sep + 'lib' + os.sep
        
        
        pylib = ''
        if os.path.exists(pylib_root + test): pylib = pylib_root + test
        else: 
            for path in sys.path:
                index = path.rfind(python_version)
                if index > 0: pylib = path[0:index+len(python_version)]
        
        if not pylib:
            print("Error on platform '" + platform.name + \
            "': Path to the default Python library not found.")
            return
            
        #Copy Files
        self.scp.copy(player, 50, 'player', dest)
        self.scp.copy(pylib + os.sep, 80, 'python', dest + os.sep + blender_version + os.sep + test)
        if platform.type_build == 'win':
            exclude = []
            src = os.path.dirname(bpy.app.binary_path) + os.sep
            for file in os.listdir(src):
                if not file.endswith('.dll'):
                    exclude.append(src + file)
                    
            self.scp.copy(src, 85, 'DLLs', dest, exclude)
                
        
        game_player = dest + os.path.basename(player)
        st = os.stat(game_player)
        os.chmod(game_player, st.st_mode | stat.S_IEXEC)
        
      

################################### DOWNLOAD RESOURCES ###################################
import time
import shutil
class DownloadProcess(threading.Thread):
    system = None
    architecture = None
    item = None
    type = None
    official = False
    
    magicURL = "http://pastebin.com/raw.php?i=KkNUhUGy"
    message = None
    
    def run(self):
        print("BUILD GAME ADDON: Starting download of " + self.item + "...")
        if self.official and self.type == "player":
            self.download_from_blender_directory()

        else: self.download_from_addon_directory()

        self.message = None
        check(self, self.context)

    def download_from_blender_directory(self):
        self.message = "Checking repository..."
        version = bpy.app.version_string.split()[0]
        baseurl = "http://download.blender.org/release/Blender" + version + '/'

        #Conversions
        if self.system == "win":
            realname = "windows"
            arch = {self.architecture[1:] + '.'}
        else:
            if self.system == "lin": realname = "linux"
            if self.system == "mac": realname = "OSX"
            if self.architecture == "x32": arch = {"i386", "i686"}
            else: arch = {"x86_64"}

        data = str(urllib.request.urlopen(baseurl).read())
        links = re.findall('"(?<=href=")(.*?)(?=">)"', data)

        for link in links:
            if realname in link and version + bpy.app.version_char in link and in_any(arch, link):
                if in_any(link.split('.'), {'tar','zip','bz2'}):
                    xname = link

        if not xname:
            print("BUILD GAME #003: Release not found")
            return
        
        #Download
        print("Downloading " + baseurl + xname + "...")
        archive = self.downloadSource(baseurl + xname)
        #archive = bpy.utils.user_resource('DATAFILES', 'platform') + os.sep + xname

        #Install
        print("Unpacking...")
        self.message = "Installing..."
        basepath = bpy.utils.user_resource('DATAFILES', 'platform') + os.sep
        tmppath = basepath + "temp" + os.sep
        os.rename(archive, basepath + xname)
        archive = basepath + xname

        shutil.unpack_archive(archive, tmppath)

        #Copy the standard files
        dest = basepath + self.system + self.architecture[1:] + os.sep + self.item + os.sep
        
        #NOTE: MacOS uses a complete diferent file structure
        os.rename(tmppath + os.listdir(tmppath)[0], dest)

        #Clean this mess.
        print("Cleaning...")
        os.rmdir(tmppath)
        try:
            shutil.rmtree(dest + version + os.sep + "datafiles")
            shutil.rmtree(dest + version + os.sep + "scripts")
            shutil.rmtree(dest + "icons", True)
            shutil.rmtree(dest + "lib", True)
            for filename in os.listdir(dest):
                if not in_any({".dll",".txt","blenderplayer", version}, filename):
                    filepath = dest + filename
                    if os.path.isfile(filepath): os.remove(filepath) 

            os.rename(dest + "copyright.txt", dest + "blender-copyright.txt")
            print("Done.")
        
        except Exception as ex:
            print(ex)


    def download_from_addon_directory(self):
        self.message = "Getting file links..."
        response = urllib.request.urlopen(self.magicURL)
        
        try:
            link = self.getLink(response)
            if not link: raise Exception ("BUILD GAME #004: Aborted! No links found for this configuration.")
            
            print(link)
            self.message = "Starting download..."
            filepath = self.downloadSource(link)
            
            zip = zipfile.ZipFile(filepath)
            zip.extractall(os.path.dirname(filepath))
            zip.close()

            print("Done.")
            
        except Exception as ex:
            print(ex)
            self.message = None
            return
        
    def getLink(self, response):
        state_platform = False
        state_item = False

        while True:
            line = response.readline()
            if not line: break
            
            line = line[:len(line)-2]
            plat = str.encode(self.system + self.architecture)
            
            if line[0] == 64 and line[1:] == plat:
                state_platform = True
            
            if state_platform == True:
                if state_item == True:
                    return line.decode()
                
                item = str.encode(self.item)
                if line[0] == 58 and line[1:] == item:
                    state_item = True
           

    def downloadSource(self, link):
        filepath = bpy.utils.user_resource('DATAFILES', "platform") + os.sep + "temp.zip"
        source = urllib.request.urlopen(link)
        file = open(filepath, 'wb+')
        filesize = source.info()['Content-Length']
        
        size = 0
        block = 4096
        start_time = time.time()
        while True:
            buffer = source.read(block)
            if not buffer:
                break
            
            file.write(buffer)
            size += len(buffer)
            percent = size/int(filesize)
            time_diff = time.time() - start_time
            if (percent > 0.01):
                estimated_time = int(time_diff / percent - time_diff)
                self.message = str(int(percent*100)) + "% - " + str(estimated_time) + " sec"
            else: self.message = str(int(percent*100)) + '%'
        file.close()
        return filepath



###################################### INTERFACE ######################################### 

class RENDER_PT_BuildGame(bpy.types.Panel):
    bl_label = "Build Game"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene and (scene.render.engine == "BLENDER_GAME")
        
    def draw(self, context):
        bs = context.scene.ge_build_settings
        layout = self.layout
        
        layout.prop(bs, 'game_name')
        layout.prop(bs, 'build_filepath')

        if BuildGame.thread.status == "":
            layout.operator("export.build_game")
        else:
            layout.operator("export.build_game_cancel")

        

class RENDER_PT_Platforms(bpy.types.Panel):
    bl_label = "Platforms"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    enabled = True
    player_exist = True
    launcher_exist = True
    
    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene and (scene.render.engine == "BLENDER_GAME")
    
    def draw(self, context):
        bs = context.scene.ge_build_settings
        layout = self.layout
        
        row = layout.row()
        if bpy.app.version[1] >= 66: row.template_list("UI_UL_list", "platforms_list", bs, 'platforms', bs, 'platforms_active')
        else: row.template_list(bs, 'platforms', bs, 'platforms_active')
        
        col = row.column(align=True)
        col.operator(BuildAddPlatform.bl_idname, icon='ZOOMIN', text="")
        col.operator(BuildRemovePlatform.bl_idname, icon='ZOOMOUT', text="")
        
        if len(bs.platforms) > bs.platforms_active >= 0:
            platform = bs.platforms[bs.platforms_active]
            row = layout.row()
            row.prop(platform, 'active')
            row.prop(platform, 'overwritte')
            row.enabled = self.enabled
            
            layout.prop(platform, 'type_build', expand=True)
            if (platform.type_build == 'custom'):
                layout.prop(platform, 'name')
                layout.prop(platform, 'custom_player_path')
                layout.prop(platform, 'custom_launcher_path')
               
            else:
                layout.prop(platform, 'default_architecture', expand=True, event=True)
                layout.prop(platform, 'name')
                
                download = DownloadPlatformResource.thread
                display = (
                        download.message and
                        download.system == platform.type_build and
                        download.architecture == platform.default_architecture
                )
                
                layout.prop(platform, 'default_player')
                
                if display and download.type == 'player':
                    split = layout.split(0.33)
                    split.separator()
                    split.label(download.message)
                    
                elif not self.player_exist:
                    split = layout.split(0.33)
                    split.separator()
                    split.operator('scene.build_game_download_platform_resource').type="player"
                    split.active = not download.isAlive()    
                    
                layout.prop(platform, 'default_launcher')
                split = layout.split(0.33)
                split.separator()        
                if display and download.type == 'launcher':
                    split.label(download.message)  
                
                elif not self.launcher_exist:
                    split.operator('scene.build_game_download_platform_resource').type="launcher"
                    split.active = not DownloadPlatformResource.thread.isAlive()              
                
                if platform.type_build == 'mac': 
                    layout.label("Warning! MacOS not tested.")
                
            row = layout.row()
            
            # Not implemented yet!
            #row.prop(platform, 'build_unpack')
            #row.prop(platform, 'build_merge')

class RENDER_PT_Tools(bpy.types.Panel):
    bl_label = "Build Game Tools"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene and (scene.render.engine == "BLENDER_GAME")

    def draw(self, context):
        ts = context.scene.ge_tools_settings
        self.layout.prop(ts, 'extract_executable_path')
        self.layout.operator("export.build_extract_blend")


###################################### OPERATORS #########################################   
                
#            
#class BuildGameOp(bpy.types.Operator):
#    bl_idname = "export.build_game"
#    bl_label = "Build Game"
#    
#    def execute(self, context):
#    
#        print("Coping files...")
#        
#        original = bpy.data.filepath
#        blend_name = bpy.path.basename(original)
#        
#        filepath = bpy.path.abspath(context.scene.build_filepath)
#        if filepath == "": print("You need to select a file path")
#       
#        else:
#            if context.scene.game_name == "": context.scene.game_name = blend_name
#            if context.scene.game_name == blend_name: context.scene.game_name = blend_name.replace(".blend", "")
#            if bpy.path.basename(filepath) != "": filepath = filepath.replace(bpy.path.basename(filepath), "")
#            
#            shutil.copy2(bpy.path.abspath(context.scene.build_player_path), filepath)
#            shutil.copy2(os.path.dirname(os.path.abspath(__file__))+"/game_engine_build/config", filepath)
#            shutil.copy2(os.path.dirname(os.path.abspath(__file__))+"/game_engine_build/mygame", filepath+context.scene.game_name)
#            if os.path.exists(filepath+"/lib/") == False: shutil.copytree(os.path.dirname(os.path.abspath(__file__))+"/../../python/lib/",filepath+"lib/")
#            
#            #Copy .blend and resources
#            print("Coping resources...")
#            if (original!=""): bpy.ops.wm.save_mainfile() 			#Save changes before do anything.
#            bpy.ops.file.pack_all() 						#Pack all (don't worry, this won't be saved in the original file)
#            bpy.ops.wm.save_mainfile(filepath=filepath+blend_name) 		#Copy the file packed and open it.
#            if context.scene.build_unpack == True:
#                bpy.ops.file.unpack_all(method="USE_LOCAL") 			#Unpack the file
#                bpy.ops.wm.save_mainfile(check_existing=False) 			#Save the changes to the copy
#            if os.path.isfile(filepath+blend_name + "1"):			#Remove the security copy if exists. (Say "remove security" and everybody loses their minds) 
#                os.remove(filepath+blend_name + "1")
#            if (original!=""): bpy.ops.wm.open_mainfile(filepath=original)	#Reopen the original file.
#            
#            #Configure the config file.
#            print("Configuring...")
#            f = open(os.path.dirname(os.path.abspath(__file__))+"/game_engine_build/config","r")
#            conf = f.read(); f.close()
#            conf = conf.replace("player:", "player: " + bpy.path.basename(context.scene.build_player_path))
#            conf = conf.replace("blend:", "blend: " + blend_name)
#            m = open(filepath+"/config", "w")
#            m.write(conf); m.close()
#            
#            print("Done.") 
#        return {'FINISHED'}
  

class BuildGame(bpy.types.Operator):
    bl_idname = "export.build_game"
    bl_label = "Build"
    
    thread = PlatformInstall()
    
    def execute(self, context):  
        bs = context.scene.ge_build_settings
        
        #If .blend not exist, save it.
        if not bpy.data.filepath:
            bpy.ops.wm.save_mainfile()

        # Fill properties
        blend_name = bpy.path.basename(bpy.data.filepath).replace(".blend", "")
        if not blend_name: blend_name = "mygame"
        
        self.thread.game_name = bs.game_name
        if self.thread.game_name == "": self.thread.game_name = blend_name
        
        self.thread.game_directory = bpy.path.abspath(bs.build_filepath)
        if self.thread.game_directory == "":
            print("BUILD GAME #005: You must select a directory first.")
            return {'CANCELLED'}
        
        filepath = self.thread.game_directory
        if bpy.path.basename(filepath):
            self.thread.game_directory = filepath.replace(bpy.path.basename(filepath), "")
        
        # Run thread
        if not self.thread.isAlive():
            self.thread.context = context
            self.thread.__init__()
            self.thread.start()
        
        #self.report({'INFO'}, message)
        return {'FINISHED'}

class BuildGameCancelButton(bpy.types.Operator):
    bl_idname = "export.build_game_cancel"
    bl_label = "Cancel"
    
    def execute(self, context):
        BuildGame.thread.stopMe()
        BuildGame.thread.status = ""
        return {'FINISHED'}
       
        
class DownloadPlatformResource(bpy.types.Operator):
    bl_idname = "scene.build_game_download_platform_resource"
    bl_label = "Download" 

    type = bpy.props.StringProperty()
    thread = DownloadProcess() 
    
    def execute(self, context):
        bs = context.scene.ge_build_settings
        platform = bs.platforms[bs.platforms_active]
        
        if not self.thread.isAlive():
            self.thread.system = platform.type_build
            self.thread.architecture = platform.default_architecture
            self.thread.type = self.type
            self.thread.context = context
            if self.type == 'player':
                self.thread.item = platform.default_player
                if platform.default_player == 'blenderplayer':
                    self.thread.official = True
            if self.type == 'launcher':
                self.thread.item = platform.default_launcher
            
            self.thread.__init__()
            self.thread.start()  
        
        return {'FINISHED'}


class BuildAddDefaultPlatform(bpy.types.Operator):
    bl_idname = "scene.build_add_default_platform"
    bl_label = "Add Platform Default"

    def execute(self, context):
        platform = context.scene.ge_build_settings.platforms.add()
        
        blender_bin_path = bpy.app.binary_path
        blender_bin_dir = os.path.dirname(blender_bin_path)
        ext = os.path.splitext(blender_bin_path)[-1].lower()
        
        platform.name = bpy.app.build_platform.decode("utf-8").replace(":","_")
        
        if platform.name == 'Linux_32bit':
            platform.type_build = 'lin'
            platform.default_architecture = 'x32'
            
        if platform.name == 'Linux_64bit':
            platform.type_build = 'lin'
            platform.default_architecture = 'x64'
            
        if platform.name == 'Windows_32bit':
            platform.type_build = 'win'
            platform.default_architecture = 'x32'
        
        if platform.name == 'Windows_64bit':
            platform.type_build = 'win'
            platform.default_architecture = 'x64'

        if platform.name == 'Mac_32bit':
            platform.type_build = 'mac'
            platform.default_architecture = 'x32'
            
        if platform.name == 'Mac_64bit':
            platform.type_build = 'mac'
            platform.default_architecture = 'x64'  
        
        check_add(self, context)
        return {'FINISHED'}


class BuildAddPlatform(bpy.types.Operator):
    bl_idname = "scene.build_add_platform"
    bl_label = "Add Platform"

    def execute(self, context):
        platforms = context.scene.ge_build_settings.platforms
        if len(platforms) > 0:
            a = platforms.add()
            a.name = a.name
        else:
            BuildAddDefaultPlatform.execute(self, context)
        
        check_add(self, context)
        return {'FINISHED'}


class BuildRemovePlatform(bpy.types.Operator):
    bl_idname = "scene.build_remove_platform"
    bl_label = "Remove Platform"

    def execute(self, context):
        bs = context.scene.ge_build_settings
        if bs.platforms_active < len(bs.platforms):
            bs.platforms.remove(bs.platforms_active)
            RENDER_PT_Platforms.enabled = True
            if bs.platforms_active == len(bs.platforms) > 0:
                bs.platforms_active -= 1
            if len(bs.platforms): check(bs.platforms[bs.platforms_active], context)
            return {'FINISHED'}
        return {'CANCELLED'}


class BuildExtractBlend(bpy.types.Operator):
    bl_idname = "export.build_extract_blend"
    bl_label = "Extract .blend from exe"

    def execute(self, context):
        import struct

        ts = context.scene.ge_tools_settings
        filepath = ts.extract_executable_path

        #Get the .blend on memory
        source = open(filepath, 'rb')
        offset = source.seek(0, 2)
        offset = source.seek(offset-12, 0)
        byte_data = source.read(4)
        num = struct.unpack('>i', byte_data)[0]
        source.seek(num)
        blend_data = source.read(offset-num)

        #Write the blend
        filepath = os.path.dirname(filepath) + os.sep + "game.blend"
        dest = open(filepath, 'wb')
        dest.write(blend_data)
        dest.close()
        source.close()

        print("Finished, blend saved as game.blend on the game directory.")
        return {'FINISHED'}


###################################### PROPERTIES #########################################

class PlatformSettings(bpy.types.PropertyGroup):
    
    active = bpy.props.BoolProperty(
            name = "Active",
            description = "Whether or not to build for this platform",
            default = True,
            update = active_click,
    )
    
    user_active = bpy.props.BoolProperty(
            default = True,
    )
            
    overwritte = bpy.props.BoolProperty(
            name = "Overwritte",
            description = "Overwritte all files including resources and libraries",
            default = False,
    )
            
    type_build = bpy.props.EnumProperty(
            items = [("custom", "Custom", ""), ("win", "Windows", ""), ("lin", "Linux", ""), ("mac", "MacOS", "")],
            name = "Type",
            description = "Select an operating sistem or a custom build.",
            default = "custom",
            update = check,
    )
    
    default_architecture = bpy.props.EnumProperty(
            items = [("x32", "x32", ""), ("x64", "x64", "")],
            name = "Architecture",
            description = "Select an architecture.",
            default = "x32",
            update = check,
    )
    
    default_player = bpy.props.EnumProperty(
            items = [("blenderplayer", "blenderplayer", "")],
            name = "Player",
            description = "Select Blender player from the list",
            default = "blenderplayer",
            update = check,
    )
    
    default_launcher = bpy.props.EnumProperty(
            items = [("simple", "Simple", ""), ("qt5launcher", "BGELauncher QT5", "")],
            name = "Launcher",
            description = "Select Blender player launcher from the list",
            default = "simple",
            update = check,
    )
    
    name = bpy.props.StringProperty(
            name = "Name",
            description = "The name of the platform",
            default = "PlatformX",
    )
    
    custom_player_path = bpy.props.StringProperty(
            name = "Player",
            description = "The path to the Blender player to use for this platform",
            default = "",
            subtype = 'FILE_PATH',
            update = check,
    )
            
    custom_launcher_path = bpy.props.StringProperty(
            name = "Launcher",
            description = "The path to the launcher to use for this platform",
            default = "",
            subtype = 'FILE_PATH',
            update = check,
    )
            
    build_unpack = bpy.props.BoolProperty(
            name = "Unpack",
            description = "Organitze your resources in subfolders",
            default = True,
    )
    
    build_merge = bpy.props.BoolProperty(
            name = "Merge",
            description = "Merge the game with the Blender player. Strongly not recomended!",
            default = False,
    )

class BuildSettings(bpy.types.PropertyGroup):

    game_name = StringProperty(
        name = "Name",
        default = "",
        description = "The name of your game",
    )

    build_filepath = StringProperty(
        name = "Directory",
        description = "Select a folder to build your game",
        default = "",
        subtype = 'DIR_PATH',
    )
    
    status_bar = StringProperty(
        default = "",
    )
    
    platforms = bpy.props.CollectionProperty(type=PlatformSettings, name="Platforms")
    platforms_active = bpy.props.IntProperty(update=check)

class ToolsSettings(bpy.types.PropertyGroup):

    extract_executable_path = StringProperty(
        name = "Executable",
        default = "",
        description = "Select an executable file that contains a .blend",
        subtype = 'FILE_PATH',
    )


###################################### ADDON SETUP #########################################

from bpy.app.handlers import persistent
@persistent
def scene_loaded(dummy):
    bpy.app.handlers.scene_update_pre.remove(scene_loaded)
    if not bpy.context.scene.ge_build_settings.platforms:
        bpy.ops.scene.build_add_default_platform()
      
    #Check if this is a newer installation.
    check_new_install()
    
    #Update the platforms interface.    
    check(bpy.context.scene.ge_build_settings, bpy.context)

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.ge_build_settings = bpy.props.PointerProperty(type=BuildSettings)
    bpy.types.Scene.ge_tools_settings = bpy.props.PointerProperty(type=ToolsSettings)
    
    bpy.app.handlers.load_post.append(scene_loaded)
    bpy.app.handlers.scene_update_pre.append(scene_loaded)

def unregister():
    bpy.utils.unregister_module(__name__)
    
    del bpy.types.Scene.ge_build_settings
    #bpy.app.handlers.load_post.remove(scene_loaded)

if __name__ == "__main__":
    print ("Run script...")
    register()
