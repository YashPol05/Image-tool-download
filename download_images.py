"""Download images from a list of URLs.

Usage:
    python download_images.py URL [URL ...] [-o OUT_DIR]
    python download_images.py -f urls.txt [-o OUT_DIR]

urls.txt holds one URL per line; blank lines and lines starting with # are ignored.
"""
import argparse
import os
import sys
import urllib.request
from urllib.parse import urlparse, unquote

BLOCKED_HOSTS = ("sellercentral.amazon.com",)
CONTENT_TYPE_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
}


def read_urls(args):
    urls = list(args.urls)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    return urls


def unique_path(path):
    base, ext = os.path.splitext(path)
    n = 1
    while os.path.exists(path):
        path = f"{base}_{n}{ext}"
        n += 1
    return path


def download(url, out_dir):
    parsed = urlparse(url)
    if parsed.hostname and parsed.hostname.lower().endswith(BLOCKED_HOSTS):
        raise ValueError("downloading from Seller Central is not allowed")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get_content_type()
        if not content_type.startswith("image/"):
            raise ValueError(f"not an image (Content-Type: {content_type})")
        data = resp.read()

    name = os.path.basename(unquote(parsed.path)) or "image"
    if not os.path.splitext(name)[1]:
        name += CONTENT_TYPE_EXT.get(content_type, ".img")

    path = unique_path(os.path.join(out_dir, name))
    with open(path, "wb") as f:
        f.write(data)
    return path


def main():
    parser = argparse.ArgumentParser(description="Download images from URLs.")
    parser.add_argument("urls", nargs="*", help="image URLs")
    parser.add_argument("-f", "--file", help="text file with one URL per line")
    parser.add_argument("-o", "--out", default="images", help="output directory (default: images)")
    args = parser.parse_args()

    urls = read_urls(args)
    if not urls:
        parser.error("provide at least one URL or --file")

    os.makedirs(args.out, exist_ok=True)
    failed = 0
    for url in urls:
        try:
            print(f"OK    {url} -> {download(url, args.out)}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {url}: {e}", file=sys.stderr)

    print(f"Done: {len(urls) - failed} downloaded, {failed} failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
