# Python Built-ins #
####################
import re
import requests
import json
from pprint import pprint
import argparse

# Third-party utils #
#####################
import geoip2.database
import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr

#import MySQLdb
from py2neo import neo4j
import py2neo.error

class TestBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, ip_cidr="0.0.0.0/0", port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.color_escape = re.compile("\\x03[0-1]?[0-9]?")
        self.ip_regex = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
        self.title_regex = re.compile("\[\[[^\[\]]*\]\]")
        self.ip, self.netmask = ip_cidr.split("/")
        self.reader = geoip2.database.Reader("GeoLite2-City.mmdb")
        self.graph = neo4j.Graph()
        try:
            self.graph.schema.create_uniqueness_constraint("User", "ip")
            self.graph.schema.create_uniqueness_constraint("Topic", "name")
        except Exception:
            pass

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        print "[DEBUG] Message Received"
        a = e.arguments[0].split(":", 1)
        # Remove colors
        new = list()
        for item in a:
            new_item = self.color_escape.sub('', item)
            new.append(new_item)

        # Figure out user
        user = new[1].split("*")[1]
        user_ip = self.ip_regex.findall(user)
        if user_ip:
            # Check if user is already in the graph database
            userN = self.graph.merge_one("User", "ip", user_ip)
            try:
                response = self.reader.city(user_ip[0])
            except ValueError:
                return
            if len(userN.properties) <= 1:
                # Lookup user's location
                pprint(response.subdivisions.most_specific.name)
                pprint(response.subdivisions.most_specific.iso_code)
                userN.properties["cityName"] = response.subdivisions.most_specific.name
                userN.properties["locationCode"] = response.subdivisions.most_specific.iso_code
                userN.properties["latitude"] = response.location.latitude
                userN.properties["longitude"] = response.location.longitude
                userN.push()
            try:
                title = self.title_regex.findall(new[0])[0]
                r = requests.get("http://en.wikipedia.org/w/api.php?format=json&action=query&prop=categories&titles=%s" % title.strip("[]"))
                jdoc = json.loads(r.text)
            except IndexError:
                return

            # Add relationships to the server
            try:
                for category in jdoc["query"]["pages"].values()[0]["categories"]:
                    topic = self.graph.merge_one("Topic", "name", category["title"])
                    relation = neo4j.Relationship(userN, "EDITED", topic)
                    self.graph.create(relation)
            except KeyError:
                return
        return

    # def on_dccmsg(self, c, e):
    #     c.privmsg("You said: " + e.arguments[0])
    #
    # def on_dccchat(self, c, e):
    #     if len(e.arguments) != 2:
    #         return
    #     args = e.arguments[1].split()
    #     if len(args) == 4:
    #         try:
    #             address = ip_numstr_to_quad(args[2])
    #             port = int(args[3])
    #         except ValueError:
    #             return
    #         self.dcc_connect(address, port)

def main():
    parser = argparse.ArgumentParser(description="Track anonymous edits to the English Wikipedia")
    parser.add_argument('server', type=str)
    parser.add_argument('channel', type=str)
    parser.add_argument('nickname', type=str)
    args = parser.parse_args()
    #print("Usage: testbot <server[:port]> <channel> <nickname> <ip_range>")

    bot = TestBot(args.channel, args.nickname, args.server)
    bot.start()

if __name__ == "__main__":
    main()
