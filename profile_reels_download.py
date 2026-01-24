# note: you may face rate limit issues with this

import os
import subprocess

VIDEO_FOLDER = "videos"

def download_profile_reels(profile_name):
    print("Downloading reels...")
    subprocess.run(["instaloader", profile_name, "--reels", "+args.txt", "--dirname-pattern=" + VIDEO_FOLDER], check=True)

def delete_profile_id(profile_name):
    print("Deleting profile id...")
    try:
        os.remove(f"./{VIDEO_FOLDER}/{profile_name}_id")
    except FileNotFoundError:
        pass

def main():
    profile_name = input("Enter profile to download reels: ").strip()
    download_profile_reels(profile_name)
    delete_profile_id(profile_name)

if __name__ == "__main__":
    main()