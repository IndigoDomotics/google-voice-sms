#Google Voice SMS Plugin

This plugin allows you to send SMS messages via any number to a Google Voice account. It will also insert the last SMS message received by an account into a state in the account device that can be used as a trigger.

## Variable Updating
The Google Voice plugin can update variables (if enabled in the configuration) by using the message format "set <variablename> to <value>".  Note that variables are case sensitive.  For example, to update your thermostat via this plugin:
  create a variable heatSetpoint
  create a variable coolSetpoint
  create a variable hvacMode
  create a trigger for each of these variables on change that updates the thermostat with the variable values

  You can now send the SMS message to your GV account: "set hvacMode to cool" and "set coolSetpoint to 67" which (assuming your triggers are correct) turn on your A/C to 67 degrees.

##Downloading for use

If you are a user and just want to download and install the plugin, click on the "Download Zip" button to the right and it will download the plugin and readme file to a folder in your Downloads directory called "google-voice-sms". Once it's downloaded just open that folder and double-click on the "GoogleVoiceSMS.indigoPlugin" file to have the client install and enable it for you.

##Contributing

If you want to contribute, just fork the repository, make your changes, and issue a pull request. Make sure that you describe the change you're making thoroughly - this will help the repository managers accept your request more quickly.

##Plugin ID

Here's the plugin ID in case you need to programmatically restart the plugin:

**Plugin ID**: com.chrisandlynette.indigoplugin.googleVoiceSMS

##Terms

This plugin was originally developed by Chris Baltas who has given us permission to open-source the plugin for the community.

Perceptive Automation is hosting this repository and will do minimal management. Unless a pull request has no description or upon cursory observation has some obvious issue, pull requests will be accepted without any testing by us. We may choose to delegate commit privledges to other users at some point in the future.

We (Perceptive Automation) don't guarantee anything about this plugin - that this plugin works or does what the description above states, so use at your own risk.
