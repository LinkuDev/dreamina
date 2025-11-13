# Dreamina Multi-Account Image Generator

## 📋 Overview
Automated image generation tool using Dreamina API with multiple account support and automatic account switching when credits run out.

## 🏗️ Architecture

### Modular Structure
```
├── main_new.py          # Main orchestrator
├── config.py            # Configuration & aspect ratios
├── cookie_handler.py    # Cookie & account loading
├── prompt_loader.py     # Prompt file reading (CSV/TXT)
├── api_generator.py     # API generation & image download
├── credit_checker.py    # Credit checking via browser
├── auth_checker.py      # Authentication verification
├── browser_utils.py     # Navigation & modal handling
└── .env                 # Environment configuration
```

## 🚀 Features

### Current Implementation
✅ **Multi-account support** - Automatically load all accounts from cookies folder
✅ **Credit management** - Check credits and switch accounts automatically
✅ **API generation** - Generate images via REST API (no UI interaction)
✅ **Batch processing** - Process multiple prompts sequentially
✅ **Aspect ratio support** - Configure image dimensions via aspect ratio
✅ **Automatic downloads** - Download generated images with naming scheme
✅ **Error handling** - Robust retry logic and error recovery

### Removed (from original a.py)
❌ **UI aspect ratio selection** - Now uses API with width/height
❌ **Watermarked image scraping** - Only API generation
❌ **Complex configuration** - Simplified to env-only

## 📝 Usage

### 1. Setup Environment
Edit `.env` file:
```properties
# Required
COOKIES_FOLDER=cookies
PROMPT_FILE=prompts/your-prompts.csv
API_BASE_URL=http://localhost:8000/v1

# Generation settings
ASPECT_RATIO=16:9
IMAGE_COUNT=4

# Browser
BROWSER_HEADLESS=false
```

### 2. Prepare Prompts
Create a CSV or TXT file in `prompts/` folder:

**CSV format:**
```csv
prompt
A beautiful sunset over the ocean
A cat wearing sunglasses
```

**TXT format:**
```
A beautiful sunset over the ocean
A cat wearing sunglasses
```

### 3. Prepare Cookies
Place cookie files in `cookies/` folder:
- Format: First line = session_id, rest = JSON array of cookies
- Files are processed in alphabetical order

### 4. Run Generator
```bash
python main_new.py
```

## 🔧 Configuration

### Aspect Ratios
Supported in `config.py`:
- `AUTO` → 1328x1328
- `21:9` → 2016x864
- `16:9` → 1664x936 (default)
- `3:2` → 1584x1056
- `4:3` → 1472x1104
- `1:1` → 1328x1328
- `3:4` → 1104x1472
- `2:3` → 1056x1584
- `9:16` → 936x1664

### Credits
- Default: 5 credits per generation
- Configurable in `config.py`: `CREDITS_PER_GENERATION`

## 📂 Output Structure
```
generated/
└── {filename}_{aspect-ratio}/
    ├── 1A_filename_16-9.jpeg
    ├── 1B_filename_16-9.jpeg
    ├── 1C_filename_16-9.jpeg
    ├── 1D_filename_16-9.jpeg
    ├── 2A_filename_16-9.jpeg
    └── ...
```

Naming scheme: `{prompt#}{letter}_{filename}_{ratio}.jpeg`

## 🔄 Workflow

1. Load all accounts from cookies folder
2. Load prompts from file
3. For each account:
   - Check available credits
   - Calculate max prompts it can handle
   - Generate images via API
   - Download results
4. Switch to next account when credits exhausted
5. Continue until all prompts processed or no accounts left

## 🛠️ Modules

### `main_new.py`
- Orchestrates entire generation process
- Manages account switching
- Coordinates between modules

### `api_generator.py`
- Calls Dreamina API for image generation
- Downloads images from URLs
- Handles retries and errors

### `credit_checker.py`
- Opens browser to check account credits
- Uses Playwright to read credit display
- Returns available credits or None

### `cookie_handler.py`
- Loads cookie files from folder
- Cleans cookies for browser compatibility
- Returns list of account objects

### `prompt_loader.py`
- Reads CSV or TXT files
- Handles headers and empty lines
- Returns list of prompt strings

### `config.py`
- Centralizes all configuration
- Loads from `.env`
- Provides aspect ratio mapping

## 🆚 Differences from a.py

| Feature | a.py | main_new.py |
|---------|------|-------------|
| UI interaction | ❌ Clicks buttons | ✅ API only |
| Aspect ratio | UI selection | API with dimensions |
| Config | JSON + env | env only |
| Structure | Monolithic | Modular |
| Watermarked images | Downloads | Skipped |
| Preview scraping | Via browser | Not needed |
| Threading | ThreadPoolExecutor | Sequential |

## 🐛 Troubleshooting

### No accounts loaded
- Check `cookies/` folder exists
- Verify JSON format in cookie files
- Ensure first line is session_id

### Generation fails
- Verify API_BASE_URL is correct
- Check session_id is valid
- Ensure enough credits

### Credit check fails
- Browser might need to be visible: `BROWSER_HEADLESS=false`
- Check cookie selector: `div.credit-amount-text-tuyBBF`

## 📊 Example Run
```
🚀 Dreamina Multi-Account Image Generator
🔑 Loading accounts from 'cookies'...
   ✅ Loaded A (221).json
   ✅ Loaded A (222).json
✅ 2 account(s) ready

📝 Total prompts to generate: 10
📐 Aspect ratio: 16:9 (1664x936)
🎨 Images per prompt: 4
💰 Credits per generation: 5

👤 Account: A (221)
💰 Checking credits...
   ✅ Credits: 50
   📊 Can process: 10 prompt(s)

   🎨 Prompt 1/10 (#1)
      📝 A beautiful sunset...
      🎨 Generating 4 image(s)...
      ✅ Generated 4 image(s)
      📥 Downloading...
         ✅ Saved

🎉 Generation Complete!
✅ Processed: 10 prompt(s)
💾 Output: /path/to/generated/prompts_16-9
```

## 📦 Dependencies
- playwright
- python-dotenv
- requests
- urllib3

Install: `pip install playwright python-dotenv requests`
