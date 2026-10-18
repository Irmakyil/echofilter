from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "synthetic_incidents.csv"
rows = []

duplicate_cases = [
    ("demo_dup_01", "Fictional Cedar Bay, Lantern Street 4", "Two adults and one infant are trapped after a fictional building collapse", 10),
    ("demo_dup_02", "Fictional Pine Ridge, Maple Avenue 18", "An older adult needs urgent insulin after a fictional flood", 8),
    ("demo_dup_03", "Fictional Harborview, Beacon Road 7", "Residents need rescue from a fictional collapsed building", 7),
    ("demo_dup_04", "Fictional Stonefield, Orchard Lane 2", "A wheelchair user needs evacuation from flood water", 5),
]
variants = [
    "Urgent help needed at {address}: {need}.",
    "Please send rescue to {address}. {need}.",
    "Checking again for {address} - {need}.",
    "Help request near {address}; {need}.",
    "Can responders reach {address}? {need}.",
    "A neighbor reports {address}: {need}.",
    "Reshare: {address}, {need}.",
    "We still need help at {address}. {need}.",
    "Emergency at {address}! {need}.",
    "Please check the report for {address}: {need}.",
]
for case, (hint, address, need, amount) in enumerate(duplicate_cases, start=1):
    for i in range(amount):
        rows.append({"post_id": f"SYN-D{case}-{i+1:02d}", "username": f"demo-witness-{(i % 6)+1}",
                     "created_at": f"2026-10-18T{10 + i // 4:02d}:{(i * 7) % 60:02d}:00Z",
                     "raw_text": variants[i % len(variants)].format(address=address, need=need),
                     "retweet_count": 18 + (i * 13) % 97, "incident_hint": hint})

shadow = [
    ("Fictional Brookside, Elm Court 3", "A newborn and two adults are trapped under rubble; urgent rescue needed"),
    ("Fictional Northgate, Willow Street 9", "An elderly person needs oxygen after the fictional apartment collapse"),
    ("Fictional Southbank, River Walk 6", "A person with diabetes is out of insulin and cannot leave the flooded building"),
    ("Fictional Meadow Park, Cedar Row 11", "Wheelchair user stranded upstairs as flood water rises; please rescue"),
    ("Fictional Eastfield, Juniper Road 5", "Child and parent are trapped in a damaged fictional building"),
    ("Fictional Westhaven, Tulip Lane 14", "An injured older adult is alone and needs urgent medical help"),
    ("Fictional Highplain, Aspen Court 2", "A resident with oxygen support is stranded after the fictional storm"),
    ("Fictional Fairview, Birch Street 8", "Baby trapped in a collapsed fictional home; send search and rescue"),
    ("Fictional Lakeside, Poppy Avenue 21", "A person with limited mobility needs help escaping rising water"),
    ("Fictional Glenwood, Iris Road 10", "An older adult is injured and trapped inside the damaged house"),
    ("Fictional Redcliff, Clover Lane 1", "Urgent rescue needed for a child under debris at this fictional address"),
    ("Fictional Springvale, Robin Street 12", "Resident with a chronic condition needs urgent medical help"),
]
for i, (address, need) in enumerate(shadow, start=1):
    rows.append({"post_id": f"SYN-S{i:02d}", "username": f"quiet-witness-{i:02d}",
                 "created_at": f"2026-10-18T12:{i*3:02d}:00Z", "raw_text": f"Please help at {address}. {need}.",
                 "retweet_count": (i * 3) % 9, "incident_hint": f"demo_shadow_{i:02d}"})

incomplete = [
    "Help, people are trapped in the building after the fictional quake.",
    "Need insulin urgently, cannot get out.",
    "Flood water is rising and a child is alone upstairs.",
    "Someone is injured and needs an ambulance, location unclear.",
    "We need drinking water and medical supplies, please respond.",
    "A collapsed structure has people inside; exact street unknown.",
    "Elderly neighbor needs oxygen but we do not know the building number.",
    "Please rescue a wheelchair user stranded by flood water.",
    "There are people missing near the damaged buildings; area not specified.",
]
for i, message in enumerate(incomplete, start=1):
    rows.append({"post_id": f"SYN-I{i:02d}", "username": f"unverified-demo-{i:02d}",
                 "created_at": f"2026-10-18T13:{i*4:02d}:00Z", "raw_text": message,
                 "retweet_count": i % 4, "incident_hint": f"demo_incomplete_{i:02d}"})

noise = [
    "Thinking of everyone affected. Sending thoughts and prayers.",
    "Breaking news: the fictional storm is being discussed on television.",
    "Beautiful sunset over the bay tonight.",
    "Please watch live for the next weather update.",
    "Thank you to every volunteer helping the community.",
    "Prayers for all families in the region.",
    "The old bridge was built many years ago, according to local history.",
    "News update: officials are holding a press conference later.",
    "I hope the rain stops soon. Stay safe, everyone.",
]
for i, message in enumerate(noise, start=1):
    rows.append({"post_id": f"SYN-N{i:02d}", "username": f"community-demo-{i:02d}",
                 "created_at": f"2026-10-18T14:{i*5:02d}:00Z", "raw_text": message,
                 "retweet_count": 20 + i * 8, "incident_hint": f"demo_noise_{i:02d}"})

with OUT.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=["post_id", "username", "created_at", "raw_text", "retweet_count", "incident_hint"])
    writer.writeheader()
    writer.writerows(rows)
print(f"Wrote {len(rows)} synthetic posts to {OUT}")
