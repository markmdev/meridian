#!/bin/bash
set -euo pipefail

# Meridian Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/markmdev/meridian/main/install.sh | bash
# Or:    ./install.sh [--version X.X.X] [target-dir]

REPO="markmdev/meridian"
VERSION=""
TARGET_DIR="."
MANIFEST_FILE=".meridian/.manifest"

# Colors (disabled if not terminal)
if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' BLUE='' NC=''
fi

log() { echo -e "${GREEN}[meridian]${NC} $1"; }
warn() { echo -e "${YELLOW}[meridian]${NC} $1"; }
error() { echo -e "${RED}[meridian]${NC} $1" >&2; exit 1; }
info() { echo -e "${BLUE}[meridian]${NC} $1"; }

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --version|-v) VERSION="$2"; shift 2 ;;
    --check)
      # Check installed version
      if [[ -f ".meridian/.version" ]]; then
        echo "Installed: $(cat .meridian/.version)"
      else
        echo "Meridian not installed in current directory"
      fi
      exit 0
      ;;
    --help|-h)
      cat << 'EOF'
Meridian Installer

Usage: install.sh [OPTIONS] [target-dir]

Options:
  --version, -v VERSION   Install specific version (default: latest)
  --check                 Show installed version and exit
  --help, -h              Show this help

Examples:
  install.sh                        # Install latest to current dir
  install.sh ~/my-project           # Install latest to ~/my-project
  install.sh -v 0.0.24 .            # Install specific version
  curl -fsSL URL/install.sh | bash  # Install from web

State files preserved on update:
  - .meridian/memory.jsonl
  - .meridian/session-context.md
  - .meridian/config.yaml (merged with new defaults)
  - .meridian/required-context-files.yaml
  - .meridian/api-docs/
  - .meridian/tasks/
  - .claude/plans/
EOF
      exit 0
      ;;
    -*) error "Unknown option: $1. Use --help for usage." ;;
    *) TARGET_DIR="$1"; shift ;;
  esac
done

# Resolve target directory
if [[ ! -d "$TARGET_DIR" ]]; then
  error "Target directory does not exist: $TARGET_DIR"
fi
TARGET_DIR=$(cd "$TARGET_DIR" && pwd)

# Check dependencies
command -v curl >/dev/null 2>&1 || error "curl is required"
command -v tar >/dev/null 2>&1 || error "tar is required"
command -v python3 >/dev/null 2>&1 || error "python3 is required"

# Get version (latest if not specified)
if [[ -z "$VERSION" ]]; then
  log "Fetching latest version..."
  VERSION=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null | grep '"tag_name"' | head -1 | cut -d'"' -f4 || true)

  # Fallback: get latest tag
  if [[ -z "$VERSION" ]]; then
    VERSION=$(curl -fsSL "https://api.github.com/repos/$REPO/tags" 2>/dev/null | grep '"name"' | head -1 | cut -d'"' -f4 || true)
  fi

  if [[ -z "$VERSION" ]]; then
    error "Could not determine latest version. Specify manually with --version"
  fi
fi

# Normalize version (remove 'v' prefix if present for consistency)
VERSION="${VERSION#v}"

log "Installing Meridian v$VERSION to $TARGET_DIR"

# Check if already at this version
if [[ -f "$TARGET_DIR/.meridian/.version" ]]; then
  CURRENT=$(cat "$TARGET_DIR/.meridian/.version" | tr -d 'v')
  if [[ "$CURRENT" == "$VERSION" ]]; then
    info "Already at version $VERSION. Reinstalling..."
  fi
fi

# Download to temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT

log "Downloading..."

# Try different URL patterns
DOWNLOAD_SUCCESS=false
for url in \
  "https://github.com/$REPO/archive/refs/tags/v$VERSION.tar.gz" \
  "https://github.com/$REPO/archive/refs/tags/$VERSION.tar.gz" \
  "https://github.com/$REPO/releases/download/v$VERSION/meridian.tar.gz" \
  "https://github.com/$REPO/releases/download/$VERSION/meridian.tar.gz"
do
  if curl -fsSL "$url" -o "$TEMP_DIR/meridian.tar.gz" 2>/dev/null; then
    DOWNLOAD_SUCCESS=true
    break
  fi
done

if [[ "$DOWNLOAD_SUCCESS" == false ]]; then
  error "Could not download version $VERSION. Check if version exists."
fi

# Extract
log "Extracting..."
tar -xzf "$TEMP_DIR/meridian.tar.gz" -C "$TEMP_DIR"

# Find the extracted directory (handles different archive structures)
# GitHub archives create: meridian-VERSION/ containing the repo
EXTRACT_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "meridian*" | head -1)
if [[ -z "$EXTRACT_DIR" || ! -d "$EXTRACT_DIR" ]]; then
  error "Could not find extracted directory"
fi

# The actual Meridian files are in the meridian/ subdirectory
if [[ -d "$EXTRACT_DIR/meridian/.claude" ]]; then
  SOURCE_DIR="$EXTRACT_DIR/meridian"
elif [[ -d "$EXTRACT_DIR/.claude" ]]; then
  SOURCE_DIR="$EXTRACT_DIR"
else
  error "Could not find Meridian files (.claude directory) in archive"
fi

# State files/dirs to preserve (never delete or overwrite)
STATE_PATTERNS=(
  ".meridian/memory.jsonl"
  ".meridian/session-context.md"
  ".meridian/config.yaml"
  ".meridian/api-docs/"
  ".meridian/tasks/"
  ".meridian/.manifest"
  ".meridian/.version"
  ".claude/plans/"
)

is_state_file() {
  local file="$1"
  case "$file" in
    .meridian/memory.jsonl) return 0 ;;
    .meridian/session-context.md) return 0 ;;
    .meridian/config.yaml) return 0 ;;
    .meridian/required-context-files.yaml) return 0 ;;
    .meridian/api-docs|.meridian/api-docs/*) return 0 ;;
    .meridian/tasks|.meridian/tasks/*) return 0 ;;
    .meridian/.manifest) return 0 ;;
    .meridian/.version) return 0 ;;
    .claude/plans|.claude/plans/*) return 0 ;;
  esac
  return 1
}

# Check if this is an update or fresh install
# Detect existing installation by manifest, version file, or config
if [[ -f "$TARGET_DIR/$MANIFEST_FILE" ]]; then
  MODE="update"
  HAS_MANIFEST=true
  log "Existing installation detected, updating..."
elif [[ -f "$TARGET_DIR/.meridian/.version" || -f "$TARGET_DIR/.meridian/config.yaml" ]]; then
  MODE="update"
  HAS_MANIFEST=false
  log "Existing installation detected (no manifest), updating..."
else
  MODE="install"
  HAS_MANIFEST=false
  log "Fresh installation..."
fi

# If updating with manifest, delete old managed files (except state files)
if [[ "$MODE" == "update" && "$HAS_MANIFEST" == true ]]; then
  DELETED=0
  while IFS= read -r file || [[ -n "$file" ]]; do
    [[ -z "$file" ]] && continue
    if ! is_state_file "$file" && [[ -e "$TARGET_DIR/$file" ]]; then
      rm -rf "$TARGET_DIR/$file"
      ((DELETED++)) || true
    fi
  done < "$TARGET_DIR/$MANIFEST_FILE"

  if [[ $DELETED -gt 0 ]]; then
    info "Removed $DELETED old file(s)"
  fi
fi

# Copy files and build manifest
> "$TEMP_DIR/manifest.txt"
COPIED=0

copy_dir() {
  local src_base="$1"
  local dst_base="$2"
  local prefix="$3"

  if [[ ! -d "$src_base" ]]; then
    return
  fi

  while IFS= read -r -d '' src_file; do
    rel_path="${src_file#$src_base/}"
    full_rel="$prefix$rel_path"
    dst_file="$dst_base/$rel_path"

    # Skip state files on update
    if [[ "$MODE" == "update" ]] && is_state_file "$full_rel"; then
      continue
    fi

    # Create directory and copy file
    mkdir -p "$(dirname "$dst_file")"
    cp "$src_file" "$dst_file"
    echo "$full_rel" >> "$TEMP_DIR/manifest.txt"
    ((COPIED++)) || true
  done < <(find "$src_base" -type f -print0)
}

# Copy directories
log "Installing files..."
copy_dir "$SOURCE_DIR/.claude" "$TARGET_DIR/.claude" ".claude/"
copy_dir "$SOURCE_DIR/.meridian" "$TARGET_DIR/.meridian" ".meridian/"

# Copy .mcp.json
if [[ -f "$SOURCE_DIR/.mcp.json" ]]; then
  if [[ "$MODE" == "update" && -f "$TARGET_DIR/.mcp.json" ]]; then
    # On update, merge MCP configs (preserve user's servers, add new ones)
    info "Preserving existing .mcp.json (check for new servers manually)"
  else
    cp "$SOURCE_DIR/.mcp.json" "$TARGET_DIR/.mcp.json"
    echo ".mcp.json" >> "$TEMP_DIR/manifest.txt"
    ((COPIED++)) || true
  fi
fi

info "Copied $COPIED file(s)"

# Merge config.yaml if updating and both exist
if [[ "$MODE" == "update" && -f "$TARGET_DIR/.meridian/config.yaml" && -f "$SOURCE_DIR/.meridian/config.yaml" ]]; then
  log "Merging config.yaml..."

  MERGE_OUTPUT=$(python3 - "$TARGET_DIR/.meridian/config.yaml" "$SOURCE_DIR/.meridian/config.yaml" << 'PYTHON_SCRIPT'
import sys

def parse_yaml_simple(content):
    """Simple YAML parser for flat key: value files"""
    result = {}
    for line in content.split('\n'):
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            # Remove inline comments
            if '#' in value:
                value = value.split('#')[0].strip()
            # Handle types
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            result[key] = value
    return result

def merge_configs(user_path, default_path):
    """Add missing keys from default to user config"""
    with open(user_path, 'r') as f:
        user_content = f.read()
    with open(default_path, 'r') as f:
        default_content = f.read()

    user_config = parse_yaml_simple(user_content)
    default_config = parse_yaml_simple(default_content)

    # Find keys in default that aren't in user
    new_keys = []
    for key, value in default_config.items():
        if key not in user_config:
            new_keys.append((key, value))

    if not new_keys:
        print("Config up to date")
        return

    # Append new keys to user config file
    with open(user_path, 'a') as f:
        f.write('\n# Added by Meridian v' + sys.argv[3] if len(sys.argv) > 3 else '' + '\n')
        for key, value in new_keys:
            if isinstance(value, bool):
                value = str(value).lower()
            f.write(f'{key}: {value}\n')

    print(f"Added: {', '.join(k for k, _ in new_keys)}")

if __name__ == '__main__':
    merge_configs(sys.argv[1], sys.argv[2])
PYTHON_SCRIPT
  ) || true

  if [[ -n "$MERGE_OUTPUT" ]]; then
    info "$MERGE_OUTPUT"
  fi
fi

# Write manifest and version
sort -u "$TEMP_DIR/manifest.txt" > "$TARGET_DIR/$MANIFEST_FILE" 2>/dev/null || true
echo "$VERSION" > "$TARGET_DIR/.meridian/.version"

# Make scripts executable
log "Setting permissions..."
find "$TARGET_DIR/.claude" -type f \( -name "*.py" -o -name "*.sh" \) -exec chmod +x {} \; 2>/dev/null || true

# Success
echo ""
echo -e "${GREEN}✓ Meridian v$VERSION installed successfully${NC}"
echo ""
echo "  Location: $TARGET_DIR"
echo "  Mode:     $MODE"
echo ""

if [[ "$MODE" == "install" ]]; then
  echo "Next steps:"
  echo "  1. Review .meridian/config.yaml for settings"
  echo "  2. Add your docs to .meridian/required-context-files.yaml"
  echo "  3. Open project in Claude Code - hooks activate automatically"
  echo ""
fi

if [[ "$MODE" == "update" ]]; then
  echo "Updated files are ready. State preserved:"
  echo "  - memory.jsonl"
  echo "  - session-context.md"
  echo "  - config.yaml (merged)"
  echo "  - required-context-files.yaml"
  echo "  - api-docs/"
  echo ""
fi
