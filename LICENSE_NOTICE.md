# License Notice

## Sync Scribe Studio API - License Information

This project combines multiple components with different licenses. This document provides comprehensive licensing information for all components.

### Primary License: GNU General Public License v2.0

The Sync Scribe Studio API is licensed under the GNU General Public License v2.0 (GPL v2.0) due to the incorporation of GPL v2.0 licensed components.

**This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.**

**This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.**

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

### Component Licenses

#### 1. Original No-Code Architects Toolkit Components
- **License**: MIT License
- **Copyright**: Stephen G. Pope
- **Components**: Core API framework, route registration system, authentication, utilities
- **Compatibility**: MIT is GPL v2.0 compatible

#### 2. YouTube Download Integration Components
- **License**: MIT License (original), relicensed as GPL v2.0 (in combination)
- **Copyright**: Original work by MatheusIshiyama, modifications by this project
- **Components**: YouTube downloader microservice, ytdl-core integration
- **Source**: Based on https://github.com/MatheusIshiyama/youtube-download-api

#### 3. Third-Party Dependencies
Each dependency maintains its own license. Major dependencies include:

**Python Dependencies:**
- Flask (BSD-3-Clause)
- Requests (Apache 2.0)
- Gunicorn (MIT)
- yt-dlp (Unlicense/Public Domain)
- FFmpeg integration (LGPL v2.1)

**Node.js Dependencies (YouTube Microservice):**
- Express (MIT)
- ytdl-core (MIT)
- cors (MIT)

### GPL v2.0 Compliance Requirements

#### For Distribution
If you distribute this software, you must:

1. **Provide Source Code**: Make the complete source code available to recipients
2. **Include License**: Include a copy of the GPL v2.0 license
3. **Include This Notice**: Include this license notice
4. **Preserve Copyrights**: Maintain all copyright notices
5. **Document Changes**: If you modify the code, document your changes

#### For SaaS Use
If you use this software to provide a service (SaaS), you are **not required** to distribute the source code under GPL v2.0, but you should:

1. **Internal Use**: Keep this license notice in your internal documentation
2. **Compliance**: Ensure any distributed components comply with GPL v2.0
3. **Attribution**: Provide proper attribution to original authors

### Source Code Availability

The complete source code for this project is available at:
- **Repository**: [Insert repository URL]
- **Branch**: main
- **Version Control**: Git

### Copyright Notices

#### Original Framework
```
Copyright (c) 2024 Stephen G. Pope
Licensed under MIT License
```

#### YouTube Integration Components
```
Original work Copyright (c) MatheusIshiyama
Modified work Copyright (c) 2025 Sync Scribe Studio API Project
Licensed under GPL v2.0
```

#### This Combined Work
```
Copyright (c) 2025 Sync Scribe Studio API Project
Licensed under GPL v2.0
```

### Trademark Notices

- YouTube is a trademark of Google Inc.
- Other trademarks mentioned are property of their respective owners.

### Disclaimer

This software is not affiliated with, endorsed by, or sponsored by YouTube, Google, or any other mentioned companies. The YouTube downloading functionality is provided for personal and educational use only, in compliance with YouTube's Terms of Service.

**Users are responsible for ensuring their use complies with:**
- YouTube Terms of Service
- Local copyright laws
- Any applicable regulations

### License Compatibility Matrix

| Component License | GPL v2.0 Compatible | Notes |
|-------------------|-------------------|-------|
| MIT | ✅ Yes | Can be combined with GPL v2.0 |
| Apache 2.0 | ✅ Yes | Compatible with GPL v2.0 |
| BSD-3-Clause | ✅ Yes | Compatible with GPL v2.0 |
| LGPL v2.1 | ✅ Yes | Lesser GPL is compatible |
| Unlicense/Public Domain | ✅ Yes | No restrictions |
| ISC | ✅ Yes | Similar to MIT, compatible |

### Contact Information

For licensing questions or to request source code:
- **Email**: [Insert contact email]
- **Project**: Sync Scribe Studio API
- **Maintainer**: [Insert maintainer information]

### Full License Text

The complete text of the GNU General Public License v2.0 can be found at:
https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

### Acknowledgments

This project builds upon the excellent work of:
- Stephen G. Pope (No-Code Architects Toolkit)
- MatheusIshiyama (YouTube Download API)
- The open-source community for various dependencies

---

**Last Updated**: 2025-01-27  
**Version**: 1.0.0

**Note**: This license notice applies to the combined work. Individual components may have different licenses as noted above. When in doubt, consult the specific license files in component directories.
