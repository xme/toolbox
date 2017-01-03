#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import MySQLdb as mdb

try:
        con = mdb.connect('localhost', 'root', 'rootpw', 'misp');
except:
        print "Cannot connect to MySQL server"
        exit(1);

# Search sightings
cur = con.cursor()
cur.execute("SELECT DISTINCT(attribute_id),event_id FROM sightings")
sightings = cur.fetchall()

j = []
for s in sightings:
        attr_id = str(s[0])
        event_id = str(s[1])
        cur.execute('SELECT COUNT(*) FROM sightings WHERE attribute_id = "' + attr_id + '"')
        attr_seen = cur.fetchall()[0][0]

        cur.execute('SELECT info, date FROM events WHERE id = "' + str(event_id) + '"')
        data = cur.fetchall()
        event_info = data[0][0]
        event_date = data[0][1]
        print event_date

        cur.execute('SELECT category,type,value1,value2,to_ids FROM attributes WHERE id = "' + attr_id + '"')
        data = cur.fetchall()
        attr_category = data[0][0]
        attr_type = data[0][1]
        attr_val1 = data[0][2]
        attr_val2 = data[0][3]
        attr_ids = data[0][4]

        event_data = {
                'attribute_id' : int(attr_id),
                'sightings' : int(attr_seen),
                'event' : {
                                'event_id' : int(event_id),
                                'event_info' : event_info,
                                'event_date' : str(event_date)
                        },
                'category' : attr_category,
                'type' : attr_type,
                'values' : {
                                'value1' : attr_val1,
                                'value2' : attr_val2
                        },
                'to_ids' : int(attr_ids)
        }
        j.append(event_data)

# Sort by sightings
j = sorted(j, key=lambda k: k['sightings'], reverse=True)

print json.dumps(j, indent=4)