import re
import csv
import io

with open("parse_data.py", "r") as f:
    text = f.read()

villain_match = re.search(r"villains_csv = '''(.*?)'''", text, re.DOTALL)
event_match = re.search(r"events_csv = '''(.*?)'''", text, re.DOTALL)

villains_lines = villain_match.group(1).strip().split("\n")
events_lines = event_match.group(1).strip().split("\n")

def escape_string(s):
    return s.replace('"', '\\"').replace("\n", " ")

with open("app/src/main/java/com/example/eidos/data/GameData.kt", "w") as f:
    f.write("package com.example.eidos.data\n\n")
    f.write("data class VillainStatic(val id: Int, val name: String, val level: Int, val hp: Int, val atk: Int, val def: Int, val xp: Long, val coin: Long, val description: String, val image: String)\n")
    f.write("data class RandomEvent(val id: Int, val text: String, val type: String, val value: Int)\n\n")
    
    f.write("object GameData {\n")
    f.write("    val VILLAINS = listOf(\n")
    
    for row in villains_lines:
        if row.startswith("id,"): continue
        # Format: id,name,level,hp,atk,def,xp_reward,coin_reward,description,image
        # Image is always the last token starting with AgAC or similar (no spaces)
        parts = row.split(",")
        id = parts[0]
        name = parts[1]
        level = parts[2]
        hp = parts[3]
        atk = parts[4]
        def_val = parts[5]
        xp = parts[6]
        coin = parts[7]
        image = parts[-1]
        desc = ",".join(parts[8:-1])
        
        f.write(f'        VillainStatic({id}, "{escape_string(name)}", {level}, {hp}, {atk}, {def_val}, {xp}, {coin}, "{escape_string(desc)}", "{escape_string(image)}"),\n')
    f.write("    )\n\n")

    f.write("    val EVENTS = listOf(\n")
    for row in csv.reader(io.StringIO("\n".join(events_lines))):
        if not row or row[0] == "id": continue
        id = row[0]
        text = row[1]
        type = row[2]
        val = row[3]
        f.write(f'        RandomEvent({id}, "{escape_string(text)}", "{escape_string(type)}", {val}),\n')
    f.write("    )\n")
    f.write("}\n")
