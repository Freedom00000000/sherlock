#!/usr/bin/env python3
"""
Cheater Detector – powered by Sherlock
Søger et brugernavn på dating-sites, NSFW-platforme og sociale netværk.
"""
import sys
import subprocess

# Dating-sites + sociale netværk der typisk bruges til hemmelige forhold
CHEATER_SITES = [
    # Dating
    "DanishDatingNet",
    "DenmarkPassions",
    "Nydate",
    "datingRU",
    # NSFW / voksenplatforme
    "APClips",
    "AdmireMe.Vip",
    "BongaCams",
    "ChaturBate",
    "Erome",
    "Image Fap",
    "LushStories",
    "Motherless",
    "PocketStars",
    "Pornhub",
    "RedTube",
    "RocketTube",
    "TnAFlix",
    "Xvideos",
    "YouPorn",
    "xHamster",
    # Sociale netværk (hemmelige profiler)
    "Instagram",
    "Snapchat",
    "TikTok",
    "Twitter",
    "Telegram",
    "Reddit",
    "Discord",
    "Kik",
    "Flickr",
]


def run(usernames: list[str]) -> None:
    if not usernames:
        print("Brug: python cheater_detect.py <brugernavn> [brugernavn2 ...]")
        sys.exit(1)

    site_args = []
    for site in CHEATER_SITES:
        site_args += ["--site", site]

    cmd = [
        sys.executable, "-m", "sherlock_project",
        "--nsfw",
        "--print-found",
        *site_args,
        *usernames,
    ]

    print(f"\n🔍 Søger efter: {', '.join(usernames)}")
    print(f"   Tjekker {len(CHEATER_SITES)} platforme...\n")
    subprocess.run(cmd)


if __name__ == "__main__":
    run(sys.argv[1:])
