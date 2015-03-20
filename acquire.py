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
        # Dictionary for all topics that just have too many connections to them
        self.topic_blacklist = [
            "unsourced statements",
            "weasel words",
            "All articles needing additional references",
            "Commons category with local link same as on Wikidata",
            "dead external links",
            "All articles lacking sources",
            "lacking in-text citations",
            "Commons category without a link on Wikidata",
            "mdy dates",
            "in need of updating",
            "Articles with hAudio microformats",
            "All stub articles",
            "Articles with hCards",
            "All orphaned articles",
            "All accuracy disputes",
            "lacking sources",
            "style editing",
            "Official website different in Wikidata and Wikipedia",
            "Coordinates on Wikidata",
            "containing potentially dated statements",
            "needing expert attention",
            "articles that are too technical",
            "needing addition references"
        ]

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
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
            except Exception:
                return
            if len(userN.properties) <= 1:
                # Lookup user's location
                pprint(response.subdivisions.most_specific.name)
                pprint(response.subdivisions.most_specific.iso_code)

                # Set user's properties
                userN.properties["cityName"] = response.subdivisions.most_specific.name
                userN.properties["locationCode"] = response.subdivisions.most_specific.iso_code
                userN.properties["latitude"] = response.location.latitude
                userN.properties["longitude"] = response.location.longitude
                userN.properties["country"] = response.country.names["en"]
                userN.push()
            try:
                title = self.title_regex.findall(new[0])[0]
                r = requests.get("http://en.wikipedia.org/w/api.php?format=json&action=query&prop=categories&titles=%s" % title.strip("[]"))
                jdoc = json.loads(r.text)
            except IndexError:
                return

            # Add topic relationships to the server
            try:
                for category in jdoc["query"]["pages"].values()[0]["categories"]:
                    # Strip the topic of the category title
                    title = category["title"].replace("Category:", "", 1)

                    if any(blacklisted in title for blacklisted in self.topic_blacklist):
                        continue

                    # Add the topic to the database if it doesn't exist
                    topic = self.graph.merge_one("Topic", "name", title)

                    # Create a relationship
                    relation = neo4j.Relationship(userN, "EDITED", topic)
                    self.graph.create(relation)
            except KeyError:
                return
        return

def main():
    parser = argparse.ArgumentParser(description="Track anonymous edits to the English Wikipedia and store them in a neo4j server")
    parser.add_argument('server', type=str, nargs="?", default="irc.wikimedia.org")
    parser.add_argument('channel', type=str, nargs="?", default="#en.wikipedia")
    parser.add_argument('nickname', type=str, nargs="?", default="los-bot")
    args = parser.parse_args()

    bot = TestBot(args.channel, args.nickname, args.server)
    bot.start()

if __name__ == "__main__":
    main()
