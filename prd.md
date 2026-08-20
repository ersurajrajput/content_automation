# Product Requirements Document (PRD)

## 1. Product Overview

### Product Name

**Video Automation & Multi-Platform Publisher**

### Product Type

Desktop GUI application built with Python.

### Purpose

The application will allow users to take long-form videos, automatically split them into configurable short clips, manage those clips, and publish or schedule them across multiple social media platforms from a single interface.

The initial target platforms are:

* YouTube
* Facebook
* TikTok

The application will use official platform APIs wherever available and will maintain a local database to track videos, clips, uploads, schedules, accounts, and errors.

---

# 2. Problem Statement

Currently, the process of converting long videos into short-form content and publishing them across multiple platforms requires several manual steps:

1. Select a long video.
2. Manually split the video into clips.
3. Rename and organize clips.
4. Upload each clip separately.
5. Enter titles/descriptions/captions.
6. Schedule posts individually.
7. Track which clips have already been uploaded.
8. Retry failed uploads manually.
9. Repeat the process for every platform.

This becomes inefficient when handling dozens or hundreds of clips.

The proposed application will centralize this workflow into one desktop application.

---

# 3. Product Vision

> **"Drop a long video into the application and let the system handle the rest."**

The long-term goal is to provide a reliable content automation platform where a user can:

```text
Long Video
     ↓
Automatic Processing
     ↓
Short Clips
     ↓
Metadata
     ↓
Scheduling
     ↓
YouTube ──────┐
Facebook ─────┼──→ Publishing
TikTok ───────┘
     ↓
Tracking & Analytics
```

---

# 4. Goals

## 4.1 Primary Goals

The application should:

* Provide a modern desktop GUI.
* Allow users to import long videos.
* Split videos into configurable clip durations.
* Store and manage generated clips.
* Preview clips.
* Maintain a publishing queue.
* Connect social media accounts.
* Upload videos through official APIs.
* Schedule uploads.
* Track upload status.
* Retry failed operations.
* Prevent duplicate uploads.
* Maintain detailed logs.
* Persist application state using SQLite.
* Support multiple platforms from one interface.

---

# 5. Non-Goals

The initial version will **not** attempt to:

* Automatically bypass platform restrictions.
* Use browser automation to bypass official API limitations.
* Scrape social media platforms.
* Automatically create fake accounts.
* Guarantee viral performance.
* Automatically generate copyrighted content.
* Circumvent upload/rate limits.
* Replace platform-specific creator dashboards.

Platform APIs and their respective policies will determine what functionality can actually be supported.

---

# 6. Target Users

## Primary User

Content creators who:

* Produce long-form videos.
* Want to create short-form content.
* Publish on multiple platforms.
* Need scheduled publishing.
* Handle large numbers of clips.

## Secondary Users

* Social media managers
* Small marketing agencies
* Video editors
* YouTubers
* Educational content creators
* Podcast creators
* Developers managing automated content channels

---

# 7. Supported Platforms

## Phase 1 Platforms

### YouTube

Required capabilities:

* Account authentication
* Channel selection
* Video upload
* Title
* Description
* Tags
* Visibility
* Scheduling where supported
* Upload status
* Error handling

### Facebook

Required capabilities:

* Facebook account/page authentication
* Page selection
* Video upload
* Reel publishing where supported
* Caption
* Scheduling where supported
* Upload status
* Error handling

### TikTok

Required capabilities:

* Account authentication
* Video upload
* Direct posting where permitted
* Draft/upload workflow where required
* Caption
* Privacy settings where supported
* Upload status
* Error handling

---

# 8. Application Architecture

The application will follow a modular architecture.

```text
┌─────────────────────────────────────────────┐
│                  GUI Layer                  │
│                  PySide6                   │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│              Application Layer              │
│  Queue │ Scheduler │ Video Manager │ Jobs  │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│               Service Layer                 │
│ Video │ Metadata │ Upload │ Authentication │
└──────────────────────┬──────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    YouTube         Facebook        TikTok
       API             API            API
                       │
                       ▼
                 SQLite Database
```

---

# 9. Technology Stack

## Core

| Component            | Technology                              |
| -------------------- | --------------------------------------- |
| Programming Language | Python                                  |
| GUI                  | PySide6                                 |
| Database             | SQLite                                  |
| ORM                  | SQLAlchemy                              |
| Video Processing     | FFmpeg                                  |
| HTTP/API             | Requests / HTTPX                        |
| Async Tasks          | asyncio / QThread / worker architecture |
| Authentication       | OAuth 2.0 where supported               |
| Configuration        | `.env` / encrypted local configuration  |
| Logging              | Python logging                          |
| Packaging            | PyInstaller                             |

---

# 10. GUI Requirements

The application should have a modern desktop interface.

## Main Layout

```text
┌───────────────────────────────────────────────────────────┐
│ Logo / App Name                          Settings / User   │
├──────────────┬────────────────────────────────────────────┤
│              │                                            │
│ Dashboard    │                                            │
│              │                                            │
│ Videos       │                 Main Content               │
│              │                                            │
│ Clips        │                                            │
│              │                                            │
│ Scheduler    │                                            │
│              │                                            │
│ YouTube      │                                            │
│ Facebook     │                                            │
│ TikTok       │                                            │
│              │                                            │
│ Settings     │                                            │
│ Logs         │                                            │
│              │                                            │
└──────────────┴────────────────────────────────────────────┘
```

---

# 11. Navigation

The sidebar will contain:

1. Dashboard
2. Videos
3. Clips
4. Upload Queue
5. Scheduler
6. YouTube
7. Facebook
8. TikTok
9. Settings
10. Logs

---

# 12. Dashboard

The dashboard will provide an overview of the application.

## Metrics

Display:

* Total videos
* Total clips
* Ready clips
* Queued uploads
* Successful uploads
* Failed uploads
* Scheduled uploads
* Active processing jobs

Example:

```text
┌────────────────┬────────────────┐
│ Total Videos   │ Total Clips   │
│     24         │     486       │
└────────────────┴────────────────┘

┌────────────────┬────────────────┐
│ Uploaded       │ Scheduled     │
│     312        │      84       │
└────────────────┴────────────────┘

┌────────────────┬────────────────┐
│ Failed         │ Processing    │
│      7         │       2       │
└────────────────┴────────────────┘
```

---

# 13. Video Management

Users can import long-form videos.

## Supported Actions

* Add video
* Remove video
* View metadata
* Play video
* Process video
* Generate clips
* Open containing folder
* View processing status

## Import Methods

Initial version:

* File picker
* Drag & drop

Future:

* Watch folder
* Automatic import

---

# 14. Video Processing

The existing Python video-splitting functionality will be integrated into the application.

## User Flow

```text
Select Video
      ↓
Configure Clip Duration
      ↓
Configure Output
      ↓
Start Processing
      ↓
FFmpeg Processing
      ↓
Generate Clips
      ↓
Save to Database
      ↓
Show Clips
```

## Configuration

User can specify:

* Clip duration
* Start time
* End time
* Output format
* Video quality
* Resolution
* FPS
* Audio settings
* Output directory

Example:

```text
Clip Duration: 60 seconds
Format: MP4
Resolution: Original
Quality: High
```

---

# 15. Clip Library

Every generated clip will be displayed in a central library.

Each clip should contain:

* Thumbnail
* Filename
* Duration
* Source video
* Creation date
* Processing status
* Upload status
* Platform status

Example:

```text
┌──────────────────────────────────────────────────┐
│ [Thumbnail]  clip_001.mp4                        │
│              Duration: 00:59                     │
│              Source: podcast.mp4                │
│                                                  │
│ YouTube:   ✓ Uploaded                            │
│ Facebook:  ✓ Uploaded                            │
│ TikTok:    ○ Pending                             │
│                                                  │
│ [Preview] [Schedule] [Upload] [Delete]           │
└──────────────────────────────────────────────────┘
```

---

# 16. Clip Status System

Each clip will have a lifecycle.

```text
CREATED
   ↓
PROCESSING
   ↓
READY
   ↓
QUEUED
   ↓
UPLOADING
   ↓
UPLOADED
```

Failure state:

```text
UPLOADING
   ↓
FAILED
   ↓
RETRY
   ↓
UPLOADING
```

Possible statuses:

* Pending
* Processing
* Ready
* Queued
* Uploading
* Uploaded
* Scheduled
* Failed
* Cancelled
* Archived

---

# 17. Upload Queue

The upload queue will manage all publishing tasks.

Example:

```text
┌────────────┬───────────┬──────────────┬────────────┐
│ Clip       │ Platform  │ Status       │ Action     │
├────────────┼───────────┼──────────────┼────────────┤
│ clip_001   │ YouTube   │ Uploaded ✓   │ View       │
│ clip_002   │ TikTok    │ Uploading    │ Cancel     │
│ clip_003   │ Facebook  │ Queued       │ Remove     │
│ clip_004   │ YouTube   │ Failed       │ Retry      │
└────────────┴───────────┴──────────────┴────────────┘
```

---

# 18. Metadata Management

Each clip can have platform-specific metadata.

## YouTube

* Title
* Description
* Tags
* Category
* Privacy
* Thumbnail

## Facebook

* Caption
* Hashtags
* Page
* Reel/video type

## TikTok

* Caption
* Hashtags
* Privacy
* Posting mode

---

# 19. Metadata Templates

Users should be able to create reusable templates.

Example:

```text
Title Template:

{source_name} - Part {clip_number}

Description:

Watch the full video here:
{source_url}

#shorts #{topic}
```

Available variables:

```text
{filename}
{source_name}
{clip_number}
{duration}
{date}
{time}
{topic}
{platform}
```

---

# 20. Scheduler

The scheduler will allow users to define publishing times.

Example:

```text
Clip 001 → YouTube  → 10:00 AM
Clip 002 → TikTok    → 01:00 PM
Clip 003 → Facebook  → 04:00 PM
Clip 004 → YouTube   → 07:00 PM
```

## Scheduling Modes

### Manual

User selects date/time for each clip.

### Sequential

Application automatically assigns times.

### Recurring

Example:

```text
Start:
22 August 2026

Frequency:
Every 4 hours

Platforms:
YouTube + Facebook + TikTok
```

---

# 21. Automatic Scheduling

The user can configure rules.

Example:

```text
Number of clips: 50

Start time:
10:00 AM

Interval:
4 hours

Platforms:
YouTube
Facebook
TikTok
```

The application generates the schedule automatically.

---

# 22. Platform Account Management

Users can connect multiple accounts.

Example:

```text
Connected Accounts

YouTube
✓ My Channel

Facebook
✓ My Page

TikTok
✓ My Account
```

Future versions may support multiple accounts per platform.

---

# 23. Authentication

Authentication must use official platform authentication mechanisms.

The application should:

* Open browser authentication when required.
* Receive OAuth callback.
* Store tokens securely.
* Refresh tokens where supported.
* Detect expired/revoked authentication.
* Prompt user to reconnect when required.

Passwords should never be stored.

---

# 24. Upload Engine

All platforms will use a common uploader interface.

Conceptually:

```python
class PlatformUploader:

    def authenticate(self):
        pass

    def upload(self, video, metadata):
        pass

    def get_status(self, upload_id):
        pass

    def cancel(self, upload_id):
        pass
```

Platform implementations:

```text
BaseUploader
     │
     ├── YouTubeUploader
     ├── FacebookUploader
     └── TikTokUploader
```

This allows new platforms to be added later without modifying the entire application.

---

# 25. Retry System

Failed uploads should automatically retry.

Example:

```text
Attempt 1 → Failed
      ↓
Wait 30 seconds
      ↓
Attempt 2 → Failed
      ↓
Wait 2 minutes
      ↓
Attempt 3 → Success
```

Maximum retry attempts should be configurable.

Default:

```text
Maximum retries: 3
```

---

# 26. Duplicate Prevention

The application must prevent accidental duplicate uploads.

Each clip should have a unique identifier/hash.

Example:

```text
SHA-256:
abc123...
```

Before uploading:

```text
Does this clip already have an upload record
for this platform/account?

YES → Skip
NO  → Upload
```

---

# 27. Logging

All important events should be logged.

Example:

```text
[10:31:02] Video imported: podcast.mp4
[10:31:04] Processing started
[10:35:21] 42 clips generated
[10:36:10] YouTube authentication successful
[10:36:15] clip_001 upload started
[10:37:02] clip_001 upload successful
```

Log levels:

* INFO
* WARNING
* ERROR
* DEBUG

---

# 28. Error Handling

The application should provide human-readable errors.

Example:

```text
Upload Failed

Platform: YouTube
Clip: clip_024.mp4

Reason:
Authentication token expired.

Action:
[Reconnect Account]
[Retry]
```

Instead of exposing raw exceptions to the user.

---

# 29. Database

SQLite will be used initially.

## Main Tables

### videos

```text
id
filename
path
duration
size
created_at
status
```

### clips

```text
id
video_id
filename
path
start_time
end_time
duration
status
hash
created_at
```

### accounts

```text
id
platform
account_name
account_identifier
access_token
refresh_token
token_expiry
created_at
```

### uploads

```text
id
clip_id
account_id
platform
remote_id
status
error
attempts
uploaded_at
```

### schedules

```text
id
clip_id
account_id
scheduled_at
status
created_at
```

### settings

```text
key
value
```

---

# 30. Automation Engine

The application will contain a background automation engine.

Example:

```text
Watch Folder
     ↓
New Video Detected
     ↓
Create Processing Job
     ↓
Generate Clips
     ↓
Create Upload Jobs
     ↓
Apply Metadata
     ↓
Generate Schedule
     ↓
Upload
     ↓
Verify
     ↓
Update Database
```

The GUI must remain responsive while these operations run.

---

# 31. Background Processing

Heavy operations must not block the GUI thread.

Operations such as:

* FFmpeg processing
* Video thumbnail generation
* Uploading
* API requests
* Scheduling
* Database operations

should run through background workers/tasks.

The UI should display progress.

---

# 32. Progress Tracking

Video processing:

```text
Processing video...

██████████████████░░ 90%

42 / 48 clips generated
```

Upload:

```text
Uploading clip_024.mp4

████████████░░░░░░░░ 65%

650 MB / 1 GB
```

---

# 33. Settings

The settings page should contain:

### General

* Application theme
* Default video directory
* Default clips directory
* Archive directory

### Processing

* Default clip duration
* Output format
* Quality
* Resolution

### Upload

* Maximum concurrent uploads
* Retry count
* Retry delay

### Scheduler

* Default interval
* Default publishing hours

### Platform

* Connected accounts
* API configuration

---

# 34. Security Requirements

The application must:

* Never store platform passwords.
* Protect OAuth tokens.
* Avoid exposing access tokens in logs.
* Mask sensitive configuration values.
* Use HTTPS APIs.
* Validate uploaded file paths.
* Restrict access to local credential storage where possible.

---

# 35. File Management

Recommended directory structure:

```text
VideoAutomator/
│
├── videos/
│
├── clips/
│
├── thumbnails/
│
├── archive/
│
├── logs/
│
├── database/
│
└── credentials/
```

---

# 36. Archive System

After successful publishing, users can configure:

```text
○ Keep original clips
● Move uploaded clips to archive
○ Delete uploaded clips
```

Default:

**Move to archive.**

The application should never permanently delete content automatically without explicit user configuration.

---

# 37. Notifications

The application should notify users when important events occur.

Examples:

* Processing completed
* Upload successful
* Upload failed
* Authentication expired
* Scheduled upload completed
* Queue completed

Initial version:

* In-app notifications

Future:

* Desktop notifications
* Email
* Telegram/Discord notifications

---

# 38. Search & Filtering

Users should be able to filter clips by:

* Filename
* Source video
* Platform
* Status
* Date
* Upload status

Example:

```text
Search: podcast

Platform:
[All ▼]

Status:
[Ready ▼]
```

---

# 39. Bulk Operations

Users should be able to select multiple clips.

Actions:

* Upload
* Schedule
* Delete
* Archive
* Change metadata
* Retry
* Cancel

Example:

```text
☑ clip_001
☑ clip_002
☑ clip_003
☐ clip_004

[Upload Selected]
[Schedule Selected]
[Archive Selected]
```

---

# 40. MVP Scope

The first usable release should contain:

### GUI

* Main window
* Sidebar
* Dashboard
* Video page
* Clip page
* Settings
* Logs

### Video

* Import video
* Split video
* Configure clip duration
* Generate thumbnails
* Preview clips

### Database

* SQLite
* Video records
* Clip records
* Upload records
* Settings

### Upload

* YouTube integration
* Upload queue
* Upload progress
* Retry mechanism

### Scheduling

* Manual scheduling
* Sequential scheduling

---

# 41. Version 2

After MVP:

* Facebook integration
* TikTok integration
* Automatic scheduling
* Metadata templates
* Watch folder
* Bulk operations
* Better analytics
* Multiple accounts

---

# 42. Version 3

Advanced automation:

* Automatic captions
* AI-generated titles
* AI-generated descriptions
* AI-generated hashtags
* Automatic thumbnail generation
* Content categorization
* Smart clip selection
* Performance analytics
* Automatic scheduling based on historical performance

---

# 43. Future AI Features

The application can eventually analyze the long-form video and automatically identify interesting sections.

Example:

```text
2-hour podcast
       ↓
AI Analysis
       ↓
Potential clips

Clip 01 → 94% interesting
Clip 02 → 89%
Clip 03 → 76%
Clip 04 → 41%
```

The user could select:

```text
Minimum Score: 80%
```

and the application would only generate/publish high-scoring clips.

This should be considered a future feature rather than part of the initial MVP.

---

# 44. User Journey

## First Launch

```text
Launch Application
       ↓
Welcome Screen
       ↓
Configure Video Folder
       ↓
Connect Platform Account
       ↓
Dashboard
```

## Creating Content

```text
Import Long Video
       ↓
Select Clip Duration
       ↓
Generate Clips
       ↓
Review Clips
       ↓
Select Platforms
       ↓
Add Metadata
       ↓
Schedule
       ↓
Publish
```

---

# 45. Example Complete Workflow

User selects:

```text
Video:
Podcast_Episode_12.mp4

Duration:
01:42:30

Clip Duration:
60 seconds
```

Application generates:

```text
102 clips
```

User selects:

```text
☑ YouTube
☑ Facebook
☑ TikTok
```

Scheduling:

```text
Start: 10:00 AM
Interval: 4 hours
```

Application creates:

```text
Day 1
10:00 → clip_001
14:00 → clip_002
18:00 → clip_003
22:00 → clip_004

Day 2
10:00 → clip_005
14:00 → clip_006
...
```

The scheduler then processes the queue automatically.

---

# 46. Performance Requirements

The GUI should remain responsive while:

* Processing videos
* Generating clips
* Uploading videos
* Scheduling jobs

The application should support:

* Large video files
* Hundreds of clips
* Large upload queues
* Interrupted operations
* Application restart without losing queue state

---

# 47. Reliability Requirements

If the application closes unexpectedly:

```text
Before crash:

clip_001 → Uploaded
clip_002 → Uploaded
clip_003 → Uploading
clip_004 → Queued
```

After restart:

```text
clip_001 → Uploaded
clip_002 → Uploaded
clip_003 → Retry
clip_004 → Queued
```

The application must recover from the database state instead of starting over.

---

# 48. Packaging

The application should eventually be distributed as a desktop executable.

Target platforms:

### Initial

* Windows

### Future

* Linux
* macOS

Potential packaging:

```text
VideoAutomator.exe
```

The user should not need to manually install Python to run the packaged version.

FFmpeg dependency should also be bundled or configured during installation.

---

# 49. Project Development Phases

## Phase 1 — Foundation

* Project structure
* PySide6 setup
* Main window
* Sidebar
* Routing/page system
* Theme
* SQLite
* SQLAlchemy
* Logging

## Phase 2 — Video Engine

* Video import
* FFmpeg integration
* Clip duration configuration
* Clip generation
* Progress tracking
* Thumbnail generation

## Phase 3 — Clip Management

* Clip library
* Preview
* Search
* Filtering
* Bulk selection
* Status management

## Phase 4 — YouTube

* Google OAuth
* Account connection
* Upload engine
* Metadata
* Upload tracking
* Error handling

## Phase 5 — Facebook

* Meta authentication
* Page management
* Video/Reel publishing
* Upload tracking

## Phase 6 — TikTok

* TikTok authentication
* Content Posting API
* Direct posting/draft workflow
* Upload tracking

## Phase 7 — Scheduler

* Queue
* Calendar
* Scheduling
* Recurring rules
* Automatic publishing

## Phase 8 — Automation

* Watch folder
* Automatic processing
* Automatic scheduling
* Automatic uploads
* Retry engine

## Phase 9 — Advanced Features

* Metadata templates
* Analytics
* Notifications
* Multiple accounts
* AI features

## Phase 10 — Production

* Testing
* Security audit
* Performance optimization
* Packaging
* Installer
* Documentation

---

# 50. MVP Acceptance Criteria

The MVP will be considered successful when a user can:

1. Launch the desktop application.
2. Import a long video.
3. Configure a clip duration.
4. Generate multiple clips.
5. View generated clips.
6. Preview clips.
7. Store clip information persistently.
8. Connect a YouTube account.
9. Upload a clip to YouTube.
10. View upload progress.
11. See the upload status.
12. Retry a failed upload.
13. Schedule a clip.
14. Close and reopen the application without losing queue information.
15. View application logs.

---

# 51. Success Metrics

The product should eventually be measured by:

* Average time saved per video
* Number of clips processed
* Successful upload percentage
* Failed upload percentage
* Average processing time
* Average upload time
* Number of active connected accounts
* Number of scheduled posts
* Application crash rate

Target initial reliability:

**≥ 95% successful automated processing/upload jobs**, excluding failures caused by platform-side restrictions, invalid credentials, unsupported content, or network outages.

---

# 52. Key Product Principle

The application should be designed around one central principle:

> **The user should configure the workflow once and let the application handle repetitive work automatically.**

The system should therefore prioritize:

**Automation → Reliability → Visibility → Control**

rather than simply providing separate upload buttons for each platform.

---

# 53. Initial Development Target

The first development milestone will be:

```text
┌──────────────────────────────────────────┐
│          VIDEO AUTOMATOR v0.1            │
├────────────┬─────────────────────────────┤
│ Dashboard  │                             │
│ Videos     │  Import Long Video          │
│ Clips      │           ↓                 │
│ Settings   │  Select Clip Duration       │
│ Logs       │           ↓                 │
│            │  Generate Clips             │
│            │           ↓                 │
│            │  View Clip Library          │
└────────────┴─────────────────────────────┘
```

**Milestone 1 goal:** Build a polished PySide6 desktop application and integrate the existing Python video-splitting engine.

After that foundation is stable, the publishing layer will be added platform-by-platform, starting with **YouTube**, followed by **Facebook** and **TikTok**.
