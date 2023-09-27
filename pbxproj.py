# -*- coding: utf-8 -*-
import json
import os
class PbxprojParsing:
    #修改打包ipa的环境
    def ipaPbxproj(self, pbxprojPath, bundleIdentifier, provisioning_profile, provisioning_profile_specifier, development_team, code_sign_identity, target_name):
        CODE_SIGN_STYLE = "Manual"
        pbxproj = self.__convertProject(pbxprojPath)
        
        rootObjectKey = pbxproj["rootObject"]
        for targetKey in pbxproj["objects"][rootObjectKey]["targets"]:
            if not target_name == "" and not pbxproj["objects"][targetKey]["name"] == target_name:
                continue
                
            buildConfigurationListKey = pbxproj["objects"][targetKey]["buildConfigurationList"]
            buildConfigurationsKey = pbxproj["objects"][buildConfigurationListKey]["buildConfigurations"]
            for key in buildConfigurationsKey:
                pbxproj["objects"][key]["buildSettings"]["PROVISIONING_PROFILE"] = provisioning_profile
                #描述文件名字
                pbxproj["objects"][key]["buildSettings"]["PROVISIONING_PROFILE_SPECIFIER"] = provisioning_profile_specifier
                pbxproj["objects"][key]["buildSettings"]["PROVISIONING_PROFILE_SPECIFIER[sdk=iphoneos*]"] = provisioning_profile_specifier
                pbxproj["objects"][key]["buildSettings"]["PROVISIONING_PROFILE_SP_ECIFIER"] = provisioning_profile_specifier
                #证书的team id
                pbxproj["objects"][key]["buildSettings"]["DEVELOPMENT_TEAM"] = development_team
                #设置证书为手动
                pbxproj["objects"][key]["buildSettings"]["CODE_SIGN_STYLE"] = CODE_SIGN_STYLE
                #验证身份
                pbxproj["objects"][key]["buildSettings"]["CODE_SIGN_IDENTITY"] = code_sign_identity
                pbxproj["objects"][key]["buildSettings"]["CODE_SIGN_IDENTITY[sdk=iphoneos*]"] = code_sign_identity
                #bundle identifier
                pbxproj["objects"][key]["buildSettings"]["PRODUCT_BUNDLE_IDENTIFIER"] = bundleIdentifier
        
        with open("%s.json" %(pbxprojPath), "w") as f:
            json.dump(pbxproj, f)
            f.close()

        os.system("plutil -convert xml1 -s -r -o %s %s.json" %(pbxprojPath, pbxprojPath))
        os.system('rm -fr %s.json' %(pbxprojPath))
        
    #修改framework的环境
    def frameworkPbxproj(self, pbxprojPath, plist, machType, isBitCode, debug_symbols):
        CODE_SIGN_STYLE = "Manual"
        CODE_SIGN_IDENTITY = "iPhone Distribution"
        pbxproj = self.__convertProject(pbxprojPath)
        objectKeys = self.__getObjectKeys(pbxproj, plist)

        for key in objectKeys:
            #修改架构
            pbxproj["objects"][key]["buildSettings"]["MACH_O_TYPE"] = machType
            #设置证书为手动
            pbxproj["objects"][key]["buildSettings"][
                "CODE_SIGN_STYLE"] = CODE_SIGN_STYLE
            #证书为空
            pbxproj["objects"][key]["buildSettings"]["DEVELOPMENT_TEAM"] = ""
            pbxproj["objects"][key]["buildSettings"][
                "PROVISIONING_PROFILE_SPECIFIER"] = ""
            pbxproj["objects"][key]["buildSettings"][
                "PROVISIONING_PROFILE_SPECIFIER"] = ""
            pbxproj["objects"][key]["buildSettings"][
                "PROVISIONING_PROFILE_SPECIFIER[sdk=iphoneos*]"] = ""
            #发布模式
            pbxproj["objects"][key]["buildSettings"][
                "CODE_SIGN_IDENTITY"] = CODE_SIGN_IDENTITY
            pbxproj["objects"][key]["buildSettings"][
                "GCC_GENERATE_DEBUGGING_SYMBOLS"] = 'YES' if debug_symbols == 'True' else 'NO'
            pbxproj["objects"][key]["buildSettings"][
                "CODE_SIGN_IDENTITY[sdk=iphoneos*]"] = CODE_SIGN_IDENTITY
            pbxproj["objects"][key]["buildSettings"][
                "LD_MAP_FILE_PATH"] = "$(TARGET_TEMP_DIR)/$(PRODUCT_NAME)-LinkMap-$(CURRENT_VARIANT)-$(CURRENT_ARCH).txt"

            #是否支持bitcode
            pbxproj["objects"][key]["buildSettings"][
                "ENABLE_BITCODE"] = 'YES' if isBitCode == True else 'NO'
            pbxproj["objects"][key]["buildSettings"][
                "OTHER_CFLAGS"] = '-fembed-bitcode' if isBitCode == True else ''

        with open("%s.json" % (pbxprojPath), "w") as f:
            json.dump(pbxproj, f)

        os.system("plutil -convert xml1 -s -r -o %s %s.json" % (pbxprojPath, pbxprojPath))
        os.system('rm -fr %s.json' % (pbxprojPath))
        
    # 添加中文配置
    def addZH(self, pbxprojPath):
        pbxproj = self.__convertProject(pbxprojPath)
        objects = pbxproj["objects"]
        for key in objects:
            obj = objects[key]
            if obj.has_key("knownRegions"):
                lans = obj["knownRegions"]
                isZH = False
                for lan in lans:
                    if lan == "zh-Hans":
                        isZH = True
                if not isZH:
                    pbxproj["objects"][key]["knownRegions"].append("zh-Hans")
                break
            
        with open("%s.json" % (pbxprojPath), "w") as f:
            json.dump(pbxproj, f)
            
        os.system("plutil -convert xml1 -s -r -o %s %s.json" % (pbxprojPath, pbxprojPath))
        os.system('rm -fr %s.json' % (pbxprojPath))
        return isZH

    #将project.pbxproj转成json格式
    def __convertProject(self, pbxproj):
        os.system(
            "plutil -convert json -s -r -o %s.json %s" % (pbxproj, pbxproj))
        with open("%s.json" % (pbxproj), 'r') as load_f:
            pbxproj = json.load(load_f)
        return pbxproj

    #查找需要替换的key
    def __getObjectKeys(self, pbxproj, plist):
        objects = pbxproj["objects"]
        objectKeys = []
        for key in objects:
            obj = objects[key]
            if obj.has_key("buildSettings"):
                buildSettings = obj["buildSettings"]
                if buildSettings.has_key("INFOPLIST_FILE") and buildSettings[
                        "INFOPLIST_FILE"] == plist:
                    objectKeys.append(key)
        return objectKeys
