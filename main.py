# -*- coding:utf-8 -*-
import os, sys
import subprocess
from pbxproj import PbxprojParsing
import datetime

code_sign_identity = 'iPhone Distribution'

def run(path, target_name, bundle_identifier, p12_path, mobileprovision_path, password, save_path):
    result = __importCertificate(p12_path, password)
    if result == None:
        print("导入p12错误，请联系技术")
        return

    data = __parsingMobileprovision(mobileprovision_path)
    if data == None:
        print("导入描述文件错误，请联系技术")
        return
    
    pwd = os.getcwd()
    
    os.chdir(path)
    
    pbxproj = ""
    for root, _, file_name_list in os.walk("./"):
        for file_name in file_name_list:
            if file_name == "project.pbxproj":
                pbxproj = os.path.join(root, file_name)

    if len(target_name) == 0:
        pbxproj_path_list = pbxproj.split("/")
        for value in pbxproj_path_list:
            if value.endswith("xcodeproj"):
                target_name = value.split(".")[0]
                break

    pp = PbxprojParsing()
    pp.ipaPbxproj(pbxproj, bundle_identifier, data['uuid'], data['name'], data['teamID'], data['code_sign_identity'], target_name)

    # 生成打包依赖的ExportOptions.plist
    os.system('rm -fr ExportOptions.plist')
    eoString = """<?xml version="1.0" encoding="UTF-8"?> 
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"> 
    <plist version="1.0"> 
    <dict> 
      <key>generateAppStoreInformation</key>
      <false/>
      <key>compileBitcode</key> 
      <false/> 
      <key>method</key> 
      <string>app-store</string> 
      <key>provisioningProfiles</key> 
  	  <dict> 
  		<key>%s</key> 
  		<string>%s</string> 
  	  </dict> 
      <key>signingCertificate</key>
      <string>%s</string>
      <key>signingStyle</key>
      <string>manual</string>
      <key>stripSwiftSymbols</key>
      <true/>
      <key>teamID</key>
      <string>%s</string>
      <key>thinning</key>
      <string>&lt;none&gt;</string>
      <key>destination</key>
      <string>export</string>
    </dict>
    </plist>""" %(bundle_identifier, data['name'], data['code_sign_identity'], data['teamID'])

    os.system("touch ExportOptions.plist")
    with open("ExportOptions.plist",'w') as f:
        f.write(eoString)
        f.close()

    (_, _) = subprocess.getstatusoutput("security set-key-partition-list -S apple-tool:,apple: -s -k heima %s/Library/Keychains/login.keychain" %(os.environ['HOME']))
    (_, output) = subprocess.getstatusoutput('xcodebuild -scheme %s -configuration Release -sdk iphoneos clean archive -archivePath %s.xcarchive' %(target_name, target_name))
    
    if not "** ARCHIVE SUCCEEDED **" in output:
        print(output)
        return

    now_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    ipa_name = "{}_{}".format(target_name, now_time)
    saveDir = '%s/%s' %(pwd, ipa_name)
    os.system('rm -fr %s' %(saveDir))
    os.system('mkdir %s' %(saveDir))
    
    (_, output) = subprocess.getstatusoutput('xcodebuild -exportArchive -archivePath %s.xcarchive -exportOptionsPlist ExportOptions.plist -exportPath %s' %(target_name, saveDir))
    
    if not "** EXPORT SUCCEEDED **" in output:
        print(output)
        return
    
    os.system('rm -fr ExportOptions.plist')
    os.system('rm -fr %s.xcarchive' %(target_name))

    os.chdir(pwd)
    subprocess.getstatusoutput("tar czvf '{}.tar.gz' '{}'".format(ipa_name, ipa_name))
    os.system("rm -fr '{}'".format(ipa_name))
    os.system("mv '{}.tar.gz' '{}/{}.tar.gz'".format(ipa_name, save_path, ipa_name))

def __importCertificate(p12_path, password):
    os.system("security unlock-keychain -p heima $HOME/Library/Keychains/login.keychain")
    (_, output) = subprocess.getstatusoutput('security import %s -k %s/Library/Keychains/login.keychain -P "%s" -T /usr/bin/codesign' %(p12_path, os.environ['HOME'], password))
    if not output.endswith(" imported."):
        print(output)
        return False
    return True

def __parsingMobileprovision(mobileprovision_path):
    os.system('security cms -D -i %s > ua_plistfile.plist' %(mobileprovision_path))

    (_, name) = subprocess.getstatusoutput(
        '/usr/libexec/PlistBuddy -c \'print:Name\' ua_plistfile.plist')
    (_, aps_environment) = subprocess.getstatusoutput(
        '/usr/libexec/PlistBuddy -c \'print:Entitlements:aps-environment\' ua_plistfile.plist'
    )
    
    
    
    (_, expirationDate) = subprocess.getstatusoutput(
        '/usr/libexec/PlistBuddy -c \'print:ExpirationDate\' ua_plistfile.plist'
    )
    (_, teamID) = subprocess.getstatusoutput(
        '/usr/libexec/PlistBuddy -c \'print:TeamIdentifier:0\' ua_plistfile.plist'
    )
    (_, teamName) = subprocess.getstatusoutput(
        '/usr/libexec/PlistBuddy -c \'print:TeamName\' ua_plistfile.plist')
    (_, uuid) = subprocess.getstatusoutput(
        '/usr/libexec/PlistBuddy -c \'print:UUID\' ua_plistfile.plist')

    (_, application_identifier) = subprocess.getstatusoutput(
        '/usr/libexec/PlistBuddy -c \'print:Entitlements:application-identifier\' ua_plistfile.plist')

    os.system('rm -fr ua_plistfile.plist')
    if not os.path.exists("~/Library/MobileDevice/Provisioning\ Profiles/%s.mobileprovision" %(uuid)):
        os.system('cp -fr %s ~/Library/MobileDevice/Provisioning\ Profiles/%s.mobileprovision' %(mobileprovision_path, uuid)) 

    return {
        'name': name,
        'code_sign_identity': code_sign_identity,
        'expirationDate': expirationDate,
        'teamID': teamID,
        'teamName': teamName,
        'uuid': uuid,
        'application_identifier': application_identifier.replace('%s.' %(teamID), '')
    }

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
