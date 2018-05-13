#!/usr/bin/python
import os
import sys
import configparser
import datetime
import time
import twitter

CONFIG_FILE_PATH='/opt/configuration/config.properties'

def getTwitterKeys():
    config=configparser.RawConfigParser()
    config.read(CONFIG_FILE_PATH)

    twitterTokens = config.items('Twitter')
    return twitterTokens.get('KK_HOME_TOKEN'), twitterTokens.get('KK_HOME_TOKEN_KEY'), twitterTokens.get('KK_HOME_CON_SEC'), twitterTokens.get('KK_HOME_CON_SEC_KEY')

def getAMQPURL():
	config=configparser.RawConfigParser()
	config.read(CONFIG_FILE_PATH)

	return config.get('Messaging', 'CLOUDAMQP_URL')

def checkXfinitySpeed():
    a = os.popen("python /usr/local/bin/speedtest-cli --simple --server 5479").read()
    lines = a.split('\n')
    ts = time.time()
    date =datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    #if speedtest could not connect set the speeds to 0
    if "Cannot" in a:
        p = 100
        d = 0
        u = 0
    #extract the values for ping down and up values
    else:
        p = lines[0][6:11]
        d = lines[1][10:14]
        u = lines[2][8:12]
    print date,p, d, u

    #connect to twitter
    TOKEN, TOKEN_KEY, CON_SEC, CON_SEC_KEY = getTwitterKeys()

    my_auth = twitter.OAuth(TOKEN,TOKEN_KEY,CON_SEC,CON_SEC_KEY)
    twit = twitter.Twitter(auth=my_auth)

    #try to tweet if speedtest couldnt even connet. Probably wont work if the internet is down
    if "Cannot" in a:
        try:
            tweet="Hey @Comcast @ComcastCares why is my internet down? I pay for 75down\\5up in San Jose, CA? #comcastoutage #comcast"
            twit.statuses.update(status=tweet)
        except:
            pass

    # tweet if down speed is less than whatever I set
    elif eval(d)<50:
        print "trying to tweet"
        try:
            # i know there must be a better way than to do (str(int(eval())))
            tweet="Hey @Comcast why is my internet speed " + str(int(eval(d))) + "down\\" + str(int(eval(u))) + "up when I pay for 75down\\5up in San Jose, CA? @ComcastCares @xfinity #comcast #speedtest"
            twit.statuses.update(status=tweet)
        except Exception,e:
            print str(e)
            pass
    GRAPHITE_URL=""
    GRAPHITE_PORT="2003"
    a = os.popen("/bin/echo \"com.XXXXXX.home.internet.speed.ping "+ str(eval(d)) + " `date +%s`\" | /bin/nc " + GRAPHITE_URL + " " + GRAPHITE_PORT)
    a = os.popen("/bin/echo \"com.XXXXXX.home.internet.speed.download "+ str(eval(d)) + " `date +%s`\" | /bin/nc " + GRAPHITE_URL + " " + GRAPHITE_PORT)
    a = os.popen("/bin/echo \"com.XXXXXX.home.internet.speed.upload "+ str(eval(u)) + " `date +%s`\" | /bin/nc " + GRAPHITE_URL + " " + GRAPHITE_PORT)
    return

def publishToAMQP(queue, exchange, routing_key, message):
    AMQPURL=getAMQPURL()
    params = pika.URLParameters(AMQPURL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel() # start a channel
    channel.queue_declare(queue) # Declare a queue
    channel.basic_publish(exchange,
                          routing_key,
                          message)
    connection.close()

def main():
    checkXfinitySpeed()

if __name__ == '__main__':
    main()
