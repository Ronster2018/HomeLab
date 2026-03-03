# What is the ARR Stack?

The ARR Stack (Automated Radarr/Lidarr/Sonarr) is a popular collection of open-source media management applications that work together to automate your media library. When deployed on Kubernetes, it provides a scalable, containerized solution for managing your entire media workflow.


## Components Overview
Application	Description:
- Jellyfin: An open-source media system that provides a way to manage and stream your media library across various devices.
- Radarr: A movie collection manager for Usenet and BitTorrent users. It automates the process of searching for movies, downloading, and managing your movie library.
- Sonarr: Similar to Radarr but for TV shows. It keeps track of your series, downloads new episodes, and manages your collection with ease.
- Jackett: Acts as a proxy server, translating queries from other apps (like Sonarr or Radarr) into queries that can be understood by a wide array of torrent search engines.
- qBittorrent: A powerful BitTorrent client that handles your downloads. Paired with Jackett, it streamlines finding and downloading media content.
- Gluetun: A lightweight, open-source VPN client for Docker environments, supporting multiple VPN providers to secure and manage internet connections across containerized applications.



### NZBGet:
A high-performance NZB downloader that efficiently retrieves Usenet articles while using minimal system resources.

### SABnzbd:
A free, open-source, and automated Usenet binary newsreader that simplifies downloading content from Usenet.
---
### Sonarr: TV Shows
A free, open-source automated PVR (Personal Video Recorder) for **TV series**, designed for Usenet and BitTorrent users

- Automation: Monitors RSS feeds, grabs new episodes, and automatically sends them to download clients (e.g., qBittorrent, SABnzbd).
- Library Management: Scans existing library, organizes files, and renames them to a user-defined format.
- Quality Management: Automatically upgrades files to higher quality (e.g., 720p to 1080p) when available.
- Failed Download Handling: Detects failed downloads and automatically searches for another release.
- Calendar View: Displays upcoming episode releases.
---
### Radarr: Movies
An open-source, automated **movie management** and PVR (Personal Video Recorder) tool designed for Usenet and BitTorrent users

- Automatic Downloading: Searches for movies via indexers and sends them to download clients (e.g., SABnzbd, Deluge, Qbittorrent).
- Quality Management: Monitors for better quality versions (e.g., upgrading from DVD to Blu-Ray).
- Library Organization: Renames and organizes movie files automatically.
- Failed Download Handling: Automatically blacklists failed releases and attempts to download another.
- Integration: Works seamlessly with media servers like Plex.
---
### Readarr:
an open-source, automated ebook and audiobook collection manager designed for Usenet and BitTorrent users
---
### Lidarr:
an automated music collection manager for Usenet and BitTorrent users
---

### NZBHydra2:
An open-source, user-friendly meta-search application designed to centralize Usenet searches by aggregating results from multiple NZB indexers.
---

### Prowlarr:
An open-source, self-hosted indexer manager and proxy designed to streamline Usenet and torrent searching for media management applications.
---

### Bazarr:
Bazarr is a companion application to Sonarr and Radarr that manages and downloads subtitles based on your requirements.
---
### Mylar3:
An automated comic book downloader (cbr/cbz) written in Python, designed to track, manage, and download digital comics using NZB and torrent clients.
---

### Whisparr:
an open-source, automated adult movie collection manager (similar to Radarr) designed for Usenet and BitTorrent users.
---
### FlareSolverr:
an open-source, self-hosted proxy server designed to bypass Cloudflare and DDoS-GUARD protective challenges.


## qBittorrent Pod Network Policies

To restrict the qBittorrent application from being accessed or making requests that are not through the VPN a NetworkPolicy is put in place.

The IPs for the VPN were retrieved from the Gluetun container's data:

```bash
export PIA_REGION="CA Montreal"
curl -L https://raw.githubusercontent.com/qdm12/gluetun/v3.38.0/internal/storage/servers.json | jq -r ".[\"private internet access\"].servers[] | select(.region == \"$PIA_REGION\") | .ips | .[]" | sort | uniq | xargs -I% echo -e '- ipBlock:\n    cidr: %/32''
```

(Be sure to get the correct SHA for the URL based on the version of Gluetun being used, additionally update the region if needed)