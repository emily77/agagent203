# Japan Life Language School OS

This repository is the Render deployment source for the AI 日語補習班營運平台。

It now boots the verified school-platform bundle directly from files stored inside this GitHub repository, instead of downloading a runtime artifact from an external URL.

## Deployment Notes

- Render pulls this repository directly.
- The bootstrap verifies the embedded bundle SHA-256 before extracting it.
- The embedded bundle is generated from the formal school-platform export source, so future updates can follow the same cutover path without relying on tmpfiles or other temporary hosts.

## Current Focus

This deployment source is intended to keep the live school-platform stable while the broader monorepo continues to evolve.
