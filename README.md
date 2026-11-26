# Syraline-Tool

**Searchable diagnostics, clean data and file inspection — all in one workspace.**

Explore · Workflows · Setup · Catalogue · Structure

---

## Why Syraline-Tool?

Working with files, structured payloads and diagnostic lookups usually means switching between disconnected scripts, web forms and command prompts. **Syraline-Tool** brings everything into a single searchable workspace designed to move smoothly from raw input to saved output.

Press **Ctrl + K** to locate any utility immediately, supply your file or payload and inspect clear results. Every completed run from the standard set is written automatically to `Output/<tool>/` using a unique filename, letting your next step build directly on what you just produced without overwriting earlier findings.

---

## Three ways to use Syraline-Tool

### 01 · Clean and reshape structured data

Open **JSON Format**, paste a payload or select a file, and run it to get clean, readable output. Compare two documents with **JSON Diff**, target specific fields via **JSON Pointer**, or convert between tabular and structured formats using the **CSV converters**.

Compact input example:

```json
{"project":"Syraline-Tool","tools":["JSON Format","File SHA256"]}
```

Readable output example:

```json
{
  "project": "Syraline-Tool",
  "tools": [
    "JSON Format",
    "File SHA256"
  ]
}
```

*Illustrative formatting preview.*

### 02 · Inspect local files safely

Drop target files into `Input/` or pick them through the interface when supported. Run **EXIF Forensic**, **PDF Inspector** or **ZIP Inspector** to examine structure and metadata, generate a cryptographic fingerprint with **File SHA256**, or scan a directory with **Duplicate File Finder** to spot identical files.

> **Important:** A matching hash proves identical file bytes, not that a file is safe to trust or execute.

### 03 · Audit domains you own or manage

Begin with **DNS Records**, then check **SSL Certificate Info** and **HTTP Headers**. Use **Email Domain Audit** to review SPF and DMARC posture, or **Domain RDAP** to inspect registration records.

> **Note:** Live network and lookup tools depend on external services and their current availability.

---

## Quick installation (3 steps)

**Prerequisites:** 64-bit Windows and an internet connection for initial setup. You do not need to pre-install Python, Rust or Visual Studio manually — setup detects a compatible Python installation or downloads a verified portable runtime from `python.org`.

1. Extract the full archive only after reviewing its source and code.
2. Run **`setup.bat`** and wait until the runtime and prebuilt packages finish installing.
3. Run **`start.bat`** to open **Syraline-Tool**.

| Workflow stage | Script | Purpose |
| :--- | :--- | :--- |
| First-time setup | `setup.bat` | Prepares Python runtime and installs dependencies |
| Regular launch | `start.bat` | Starts the **Syraline-Tool** workspace |

Keep both `.bat` launchers beside the `Syraline-Tool` folder. If `setup.bat` reports an error, fix the issue before launching the application. If you need help getting started, reach out to the team on Discord.

---

## Workspace controls & customization

Keyboard shortcuts keep navigation fast without hunting through menus:

| Action | Control |
| :--- | :--- |
| Find a tool | `Ctrl + K` |
| Choose a theme | `F2` |
| Toggle animations | `F6` |
| Quit | `Ctrl + Q` |

* **Six languages:** Français · English · Español · Deutsch · 中文 · العربية
* **Ten themes:** Crimson · Glacier · Orchid · Ivory · Emerald · Amber · Ocean · Rose · Mono · Rainbow

---

## Complete catalogue — 78 options

### Utilities · 14 tools

Hash Tools · Password Generator · QR Code · Text Encoder · Base64 Tools · UUID Generator · Timestamp · Line Deduplicator · Unicode Inspector · Random Token · Text Diff · URL Defang · URL Refang · Tracking URL Cleaner

### Files & Media · 13 tools

EXIF Forensic · File SHA256 · ZIP Inspector · File Details · File Compare · Encoding Detector · File Hexdump · File Entropy · Local Secret Audit · PDF Inspector · QR Barcode Reader · Similar Image Finder · Duplicate File Finder

### Data & Encoding · 13 tools

JSON Format · JSON Minify · JWT Inspector · URL Decode · Hex Decode · HTML Unescape · Base64 URL Encode · CSV to JSON · JSON to CSV · XML Format · JSON Pointer · JSON Diff · TOML to JSON

### IP & Network · 9 tools

Web Lookup · IP Localisation · IP Opérateur · Open Ports · IP Pinger · IP Inspector · Subnet Calculator · Reverse DNS · CIDR Overlap

### Roblox · 9 tools

Username Lookup · Account Age · Friends Count · Followers Count · Following Count · Group Lookup · Game Lookup · Place to Universe · Avatar Info

### Domains & Infrastructure · 6 tools

WHOIS Lookup · DNS Records · Subdomain Finder · SSL Certificate Info · Domain RDAP · Email Domain Audit

### Website · 6 tools

Website Info · URL Scanner · HTTP Headers · Robots Reader · Sitemap Reader · HTTP Response

### OSINT · 6 tools

Email Info · GitHub Repository · GitHub User · Public Username Search · Phone Number Inspector · Email Header Analyzer

### Discord · 2 tools

Invite Resolver · Snowflake Decoder

---

## Clean workspace structure

```text
Syraline-Tool/
├── start.bat       Launch the toolkit
├── setup.bat       Install dependencies
├── Input/          Files to analyse and local packs
├── Output/         Exported results and screenshots
├── README.md       Project overview and launch instructions
└── Syraline-Tool/  Application code and dependency declarations
```

Relative file paths resolve from `Input/`. Local user preferences are stored in `%LOCALAPPDATA%/Syraline-Tool/settings.json`. Keep personal inputs, exported outputs and local settings out of the repository.

---

## Scope and service limits

The 78 standard tools focus on local file and data analysis, public-information queries and authorised diagnostics. Network tools must be used strictly within a scope you own or have explicit permission to test. Always respect privacy and the terms of the services you query.

Imported third-party scripts sit outside the standard catalogue. Review their origin and source code carefully before running them, as they execute with your Windows user's permissions.

---

![Syraline-Tool](./syraline.jpg)