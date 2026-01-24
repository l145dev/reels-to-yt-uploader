import subprocess

VIDEO_FOLDER = "videos"


def batch_install(posts):
    print("Downloading posts...")

    for post in posts:
        print("Downloading post: " + post)
        subprocess.run(["instaloader", f"--dirname-pattern={VIDEO_FOLDER}", "+args.txt", "--", "-" + post], check=True)

def main():
    input_posts = input("Enter posts to download separated by a comma without spaces: ").strip().split(",")
    batch_install(input_posts)

if __name__ == "__main__":
    main()