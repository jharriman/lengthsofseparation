import irc.bot
import irc.strings
import re
import geoip2.database
from pprint import pprint
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import MySQLdb
import requests
import json
from py2neo import neo4j

class TestBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, ip_cidr, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.color_escape = re.compile("\\x03[0-1]?[0-9]?")        
        self.ip_regex = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
        self.title_regex = re.compile("\[\[[^\[\]]*\]\]")
        self.ip, self.netmask = ip_cidr.split("/")
        self.reader = geoip2.database.Reader("GeoLite2-City.mmdb")
        self.db = MySQLdb.connect(host="localhost", user="jharriman", passwd="KotOR!1", db="wikipedia")
        self.cur = self.db.cursor()
        self.cur.execute("use wikipedia;");
        self.graph_db = neo4j.GraphDatabaseService()

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        # print "[DEBUG] Message Received"
        a = e.arguments[0].split(":", 1)
        # Remove colors
        new = list()
        for item in a:
            new_item = self.color_escape.sub('', item)
            new.append(new_item)

        # Figure out user
        user = new[1].split("*")[1]
        print user
        user_ip = self.ip_regex.findall(user)
        if user_ip:
            try:
                response = self.reader.city(user_ip[0])
                pprint(response.subdivisions.most_specific.name)
                pprint(response.subdivisions.most_specific.iso_code)
                print response.location.latitude, response.location.longitude
                print type(response.location.latitude)
                print self.title_regex.findall(new[0])
                try:
                    title = self.title_regex.findall(new[0])[0]
                    r = requests.get("http://en.wikipedia.org/w/api.php?format=json&action=query&prop=categories&titles=%s" % title.strip("[]"))
                    jdoc = json.loads(r.text)
                    for category in jdoc["query"]["pages"].values()[0]["categories"]:
                        indexed_node = self.graph_db.get_or_create_indexed_node("Wikipedia", "name", category["title"], { "name" : category["title"] })
                        print indexed_node
                except IndexError:
                    return
                command = "INSERT INTO EN VALUES ('%s','%s','%f','%f')" % (user.strip(), title, response.location.latitude, response.location.longitude)
                try:
                    self.cur.execute(command)
                    self.db.commit()
                except Exception:
                    pass
            except ValueError:
                pass                
        return

    def on_dccmsg(self, c, e):
        c.privmsg("You said: " + e.arguments[0])

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

def main():
    import sys
    if len(sys.argv) != 5:
        print("Usage: testbot <server[:port]> <channel> <nickname> <ip_range>")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6667
    channel = sys.argv[2]
    nickname = sys.argv[3]
    ip_cidr = sys.argv[4]

    bot = TestBot(channel, nickname, server, ip_cidr, port)
    bot.start()

if __name__ == "__main__":
    main()
