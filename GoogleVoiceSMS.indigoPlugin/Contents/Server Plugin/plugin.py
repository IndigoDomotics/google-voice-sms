#! /usr/bin/env python
# -*- coding: utf-8 -*-
########################################
# Google Voice SMS Plugin
# Developed by Chris Baltas
# Portions Copyright Joe McCal & Just Quick (googlevoice)
########################################

################################################################################
# Imports
################################################################################
from googlevoice import Voice
import os
import sys
import string
import time
import BeautifulSoup
import re

################################################################################
# Globals
################################################################################


################################################################################
class Plugin(indigo.PluginBase):

    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debug = pluginPrefs.get("showDebugInfo", False)
        self.deviceList = []
        self.shutdown = False
        self.voice = Voice()

    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    # Plugin Start and Stop methods
    ########################################

    def startup(self):
        self.debugLog("startup called")

    def shutdown(self):
        self.debugLog("shutdown called")

    ########################################
    # Device Start and Stop methods
    ########################################

    def deviceStartComm(self, device):
        self.debugLog("Starting device: " + device.name)
        if device.id not in self.deviceList:
            self.deviceList.append(device.id)

    ########################################
    def deviceStopComm(self, device):
        self.debugLog("Stopping device: " + device.name)
        if device.id in self.deviceList:
            self.deviceList.remove(device.id)


    ########################################
    # Routines for Sending SMS
    ########################################

    def sendSMSMessage (self, action):
        smsDevice = indigo.devices[action.deviceId]
        smsNumber = smsDevice.pluginProps['address']
        smsMessage = self.substitute(action.props["smsMessage"])

        try:
            indigo.server.log("Sending '"+smsMessage+"' to "+smsNumber)
            smsDevice.updateStateOnServer(key="lastAction", value="Sending")
            self.voice.send_sms(smsNumber, smsMessage)
            smsDevice.updateStateOnServer(key="lastAction", value="Success")
            indigo.server.log("Message sent successfully.")

        except:
            smsDevice.updateStateOnServer(key="lastAction", value="Error")
            indigo.server.log("Unable to send message.")

    def sendSMSMessageSingle (self, number, message):
        try:
            indigo.server.log("Sending '"+message+"' to "+number)
            self.voice.send_sms(number, message)
            indigo.server.log("Message sent successfully.")

        except:
            indigo.server.log("Unable to send message.")


    ########################################
    # Routine for parsing sms messages
    ########################################

    def extractsms(self,htmlsms):
        msgitems = []                                        # accum message items here
        #    Extract all conversations by searching for a DIV with an ID at top level.
        tree = BeautifulSoup.BeautifulSoup(htmlsms)            # parse HTML into tree
        conversations = tree.findAll("div",attrs={"id" : True},recursive=False)
        for conversation in conversations :
            #    For each conversation, extract each row, which is one SMS message.
            rows = conversation.findAll(attrs={"class" : "gc-message-sms-row"})
            for row in rows :                                # for all rows
                #    For each row, which is one message, extract all the fields.
                msgitem = {"id" : conversation["id"]}        # tag this message with conversation ID
                spans = row.findAll("span",attrs={"class" : True}, recursive=False)
                for span in spans :                            # for all spans in row
                    cl = span["class"].replace('gc-message-sms-', '')
                    msgitem[cl] = (" ".join(span.findAll(text=True))).strip()    # put text in dict
                msgitems.append(msgitem)                    # add msg dictionary to list
        return msgitems

    ########################################
    def verifyDevice(self, device, cell, msg, time):
        smsNumber = device.pluginProps['address']
        if smsNumber == cell[2:12]:
            indigo.server.log("Time: "+time+"  From: "+cell+"  MSG: "+msg+"  *authorized*")
            device.updateStateOnServer(key="receivedText", value="") # cleared in case the same message is received

            if self.pluginPrefs['gvCommandParsing'] == True:
                expression = re.compile("[Ss]et ([\w\d]+) to ([\w\d]+)")
                match = expression.match(msg)
                try:
                    var = match.group(1)
                    val = match.group(2)
                    varUpdate = True
                except:
                    varUpdate = False
                if varUpdate == True:
                    try:
                        indigo.variable.updateValue(str(var), value=str(val))
                        indigo.server.log("Updated " + str(var))
                        if self.pluginPrefs['gvReplySuccess'] == True:
                            self.sendSMSMessageSingle(cell, str(var) + ' set to ' + str(val))
                    except ValueError, e:
                        indigo.server.log('ERROR: Could not set ' + str(var) + ' to ' + str(val) + '.  Could not find variable ' + str(var))
                        if self.pluginPrefs['gvReplyError'] == True:
                            self.sendSMSMessageSingle(cell, 'Error - could not find variable ' + str(var))

            device.updateStateOnServer(key="receivedText", value=msg.lower().strip().strip('.'))
            verified = True
        else:
            verified = False

        return verified

    ########################################
    # Routines for Concurrent Thread
    ########################################

    def runConcurrentThread(self):

        self.debugLog("Starting concurrent thread")
        configRead = False
        try:
            email = self.pluginPrefs['gveMailAddress']
            passwrd = self.pluginPrefs['gvPassword']
            sleepSecs = int(self.pluginPrefs.get('gvSleepSecs', 4))
            configRead = True
        except:
            indigo.server.log("Error reading plugin configuration. (Please configure Plugin preferences)")

        if configRead:
            try:
                indigo.server.log("Logging in to your Google Voice account.")
                self.voice.login(email, passwrd)
                indigo.server.log("Successfully logged in to: "+email)
                while self.shutdown == False:
                    self.voice.sms()
                    messageReceived = False
                    for msg in self.extractsms(self.voice.sms.html):
                        unauthorized = True
                        if msg['from'] != "Me:":
                            messageReceived = True
                            for deviceId in self.deviceList:
                                verified = self.verifyDevice(indigo.devices[deviceId],msg['from'],msg['text'],msg['time'])
                                if verified: unauthorized = False
                        if msg['from'] == "Me:":
                             unauthorized = False
                        if (unauthorized==True and messageReceived==True):
                            indigo.server.log("Time: "+msg['time']+"  From: "+msg['from']+"  MSG: "+msg['text']+"  *unauthorized*")
                    if messageReceived:
                        for message in self.voice.sms().messages:
                            message.delete()
                    time.sleep (sleepSecs)
                self.voice.logout()
            except:
                indigo.server.log("Unable to login.  Please verify your e-mail/password in the plugin preferences")


    ########################################
    def stopConcurrentThread(self):
        self.debugLog("Stopping concurrent thread")
        self.shutdown = True

    ########################################
    # Preference close dialog methods
    ########################################

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if not userCancelled:
            self.debug = valuesDict.get("showDebugInfo", False)
            if self.debug:
                indigo.server.log("Debug logging enabled")
            else:
                indigo.server.log("Debug logging disabled")

    ########################################
    # Preference Validation methods
    ########################################
    # Validate the plugin config window after user hits OK
    # Returns False on failure, True on success

    def validatePrefsConfigUi(self, valuesDict):
        self.debugLog(u"validating Prefs called")
        errorsDict = indigo.Dict()
        errorsFound = False

        if len(valuesDict[u'gveMailAddress']) == 0:
            errorsDict[u'gveMailAddress'] = 'A valid Google Voice e-mail is required.'
            errorsFound = True

        if len(valuesDict[u'gvPassword']) == 0:
            errorsDict[u'gvPassword'] = 'Your Google Voice password is required.'
            errorsFound = True

        if errorsFound:
            return (False, valuesDict, errorsDict)
        else:
            return (True, valuesDict)


    ########################################
    # Device Validation methods
    ########################################
    # Validate the device config window after the user hits OK
    # Returns False on failure, True on success

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        self.debugLog(u"Device Validation called")
        errorsDict = indigo.Dict()
        errorsFound = False

        if len(valuesDict[u'address']) != 10:
            errorsDict[u'address'] = 'Phone number must be 10 digits with no special characters and no leading 1'
            errorsFound = True

        if errorsFound:
            return (False, valuesDict, errorsDict)
        else:
            return (True, valuesDict)

    ########################################
    # Action Validation methods
    ########################################
    # Validate the actions config window after the user hits OK
    # Returns False on failure, True on success

    def validateActionConfigUi(self, valuesDict, typeId, actionId):
        self.debugLog(u"Action Validation called")
        errorsDict = indigo.Dict()
        errorsFound = False

        if len(valuesDict[u'smsMessage']) == 0:
            errorsDict[u'smsMessage'] = 'Message is a required field.'
            errorsFound = True

        if errorsFound:
            return (False, valuesDict, errorsDict)
        else:
            return (True, valuesDict)
