#!/bin/bash

################################################################################
# VLP2SS - The VLP to ScreenSteps Converter
# Python Launcher Script
# 
# This script provides a convenient wrapper around the Python converter and
# uploader scripts with enhanced user experience and logging.
# This script is a wrapper around the python scripts and provides a convenient interface for the user.
# Version: 1.0.3
# Author: Burke Azbill
# License: MIT 
################################################################################

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly BOLD='\033[1m'
readonly NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default values
INPUT=""
OUTPUT="output"
VERBOSE=false
UPLOAD=false
ACCOUNT=""
USER=""
TOKEN=""
SITE=""
NO_CLEANUP=false
DRY_RUN=false
VERBOSE_FLAG="" # Initialize to empty string
SUFFIX_FLAG="" # Initialize to empty string

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${MAGENTA}${BOLD}======================================================================${NC}"
    echo -e "${MAGENTA}${BOLD}$(printf '%*s' $(((70+${#1})/2)) "$1")${NC}"
    echo -e "${MAGENTA}${BOLD}======================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}" >&2
}

print_step() {
    local step=$1
    local total=$2
    local message=$3
    echo -e "${BLUE}[${step}/${total}] ${message}${NC}"
}

print_substep() {
    echo -e "  → $1"
}

print_usage() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════╗
║              VLP2SS - The VLP to ScreenSteps Converter                   ║
║                     Python Launcher Script                               ║
╚══════════════════════════════════════════════════════════════════════════╝

USAGE:
    vlp2ss-py.sh -i <input> -o <output> [OPTIONS]

REQUIRED ARGUMENTS:
    -i, --input PATH        Input VLP ZIP file or extracted directory

OPTIONAL ARGUMENTS:
    -o, --output PATH       Output directory (default: output)
    -v, --verbose           Enable verbose logging
    --no-cleanup            Keep temporary files after conversion
    --dry-run               Show what would be done without executing
    --version               Display version information for the Python converter

UPLOAD OPTIONS:
    --upload                Upload to ScreenSteps after conversion
    --account NAME          ScreenSteps account name
    --user USER             ScreenSteps user ID
    --token TOKEN           ScreenSteps API token
    --site SITE_ID          ScreenSteps site ID
    --suffix                Append "-python" to the manual title during upload

OTHER OPTIONS:
    -h, --help              Show this help message
    --examples              Show detailed usage examples for the Python converter

EOF
}

print_examples() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════╗
║                         USAGE EXAMPLES                                   ║
╚══════════════════════════════════════════════════════════════════════════╝

1. Convert a VLP ZIP file:
   ./vlp2ss-py.sh -i HOL-2601-03-VCF-L_en.zip -o output/

2. Convert an extracted directory:
   ./vlp2ss-py.sh -i VLP-Export-Samples/HOL-2601-03-VCF-L-en/ -o output/

3. Convert with verbose output:
   ./vlp2ss-py.sh -i input.zip -o output/ -v

4. Convert and upload to ScreenSteps:
   ./vlp2ss-py.sh -i input.zip -o output/ \
       --upload \
       --account myaccount \
       --user admin \
       --token abc123xyz \
       --site 12345

5. Batch convert multiple files:
   for file in *.zip; do
       ./vlp2ss-py.sh -i "$file" -o "output/$(basename "$file" .zip)"
   done

6. Display the version of the Python converter:
   ./vlp2ss-py.sh --version

7. Show detailed usage examples for the Python converter:
   ./vlp2ss-py.sh --examples

8. Convert with environment variables for credentials:
   export SS_ACCOUNT=myaccount
   export SS_USER=admin
   export SS_TOKEN=abc123xyz
   export SS_SITE=12345
   ./vlp2ss-py.sh -i input.zip -o output/ --upload

9. Dry run to see what would happen:
   ./vlp2ss-py.sh -i input.zip -o output/ --dry-run

10. Keep temporary files for debugging:
   ./vlp2ss-py.sh -i input.zip -o output/ --no-cleanup

11. Append "-python" to the manual title during upload:
   ./vlp2ss-py.sh -i input.zip -o output/ --suffix

╔══════════════════════════════════════════════════════════════════════════╗
║                    ENVIRONMENT VARIABLES                                 ║
╚══════════════════════════════════════════════════════════════════════════╝

The following environment variables can be used instead of command-line args:

    SS_ACCOUNT      ScreenSteps account name
    SS_USER         ScreenSteps user ID
    SS_TOKEN        ScreenSteps API token
    SS_SITE         ScreenSteps site ID

Example:
    export SS_ACCOUNT=myaccount
    export SS_USER=admin
    export SS_TOKEN=abc123xyz
    export SS_SITE=12345
    ./vlp2ss-py.sh -i input.zip --upload

EOF
}

check_dependencies() {
    local missing_deps=()
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_info "Please install the missing dependencies and try again."
        exit 1
    fi
    
    # Check for Python packages
    if ! python3 -c "import requests" 2>/dev/null; then
        print_warning "Python 'requests' package not found. Installing..."
        pip3 install requests || {
            print_error "Failed to install 'requests' package"
            exit 1
        }
    fi
}

validate_input() {
    if [ -z "$INPUT" ]; then
        print_error "Input file or directory is required"
        print_info "Use -i or --input to specify the input"
        exit 1
    fi
    
    if [ ! -e "$INPUT" ]; then
        print_error "Input path does not exist: $INPUT"
        exit 1
    fi
    
    if $UPLOAD; then
        # Check for credentials in environment variables if not provided
        ACCOUNT="${ACCOUNT:-${SS_ACCOUNT:-}}"
        USER="${USER:-${SS_USER:-}}"
        TOKEN="${TOKEN:-${SS_TOKEN:-}}"
        SITE="${SITE:-${SS_SITE:-}}"
        
        if [ -z "$ACCOUNT" ] || [ -z "$USER" ] || [ -z "$TOKEN" ] || [ -z "$SITE" ]; then
            print_error "Upload requires --account, --user, --token, and --site"
            print_info "Or set environment variables: SS_ACCOUNT, SS_USER, SS_TOKEN, SS_SITE"
            exit 1
        fi
    fi
}

run_conversion() {
    print_header "VLP to ScreenSteps Conversion"
    
    print_info "Input: $INPUT"
    print_info "Output: $OUTPUT"
    
    if $DRY_RUN; then
        print_warning "DRY RUN MODE - No actual conversion will be performed"
        print_info "Would execute: python3 $SCRIPT_DIR/vlp_converter.py -i \"$INPUT\" -o \"$OUTPUT\""
        if $UPLOAD; then
            print_info "Would then upload to ScreenSteps account: $ACCOUNT"
        fi
        return 0
    fi
    
    # Detect input type
    # If input is a directory, check for content.xml (VLP) or *.html (HTML Export)
    # If input is a zip, we need to check contents or extract first.
    # The current logic extracts ZIPs inside vlp_converter.py, but for HTML we need to know before calling a converter.
    
    # Let's extract to a temp location to inspect if it's a ZIP
    local is_html_export=false
    local input_path="$INPUT"
    local temp_extract_dir=""
    
    if [ -f "$INPUT" ] && [[ "$INPUT" == *.zip ]]; then
        # It's a zip file. Let's list contents to guess type.
        # VLP export has "content.xml" at root or in a subdir.
        # HTML export has "*.html" and "images/" folder.
        
        if unzip -l "$INPUT" | grep -q "content.xml"; then
            print_info "Detected VLP Export format (content.xml found)."
            is_html_export=false
        elif unzip -l "$INPUT" | grep -q ".html"; then
            print_info "Detected HTML Export format (.html found)."
            is_html_export=true
        else
            print_warning "Could not auto-detect format. Defaulting to VLP converter."
            is_html_export=false
        fi
    elif [ -d "$INPUT" ]; then
        # It's a directory
        if [ -f "$INPUT/content.xml" ] || [ -n "$(find "$INPUT" -maxdepth 2 -name "content.xml")" ]; then
             is_html_export=false
        elif [ -n "$(find "$INPUT" -maxdepth 1 -name "*.html")" ]; then
             is_html_export=true
        fi
    fi

    if $is_html_export; then
        print_step 1 2 "Converting HTML Export to ScreenSteps format"
        
        # If it's a ZIP, we must extract it first because html_converter.py expects a file path
        if [ -f "$INPUT" ] && [[ "$INPUT" == *.zip ]]; then
            local base_name=$(basename "$INPUT" .zip)
            temp_extract_dir="temp_html_extract_${base_name}"
            mkdir -p "$temp_extract_dir"
            print_substep "Extracting ZIP to $temp_extract_dir..."
            unzip -q "$INPUT" -d "$temp_extract_dir"
            
            # Find the HTML file
            local html_file=$(find "$temp_extract_dir" -name "*.html" | head -n 1)
            if [ -z "$html_file" ]; then
                print_error "No HTML file found in zip."
                rm -rf "$temp_extract_dir"
                exit 1
            fi
            
            input_path="$html_file"
            
            # Output directory logic
            # If user specified output, use it. We append manual name to keep structure clean.
            local manual_name="${base_name}"
            local html_output="$OUTPUT/$manual_name"
            
            print_substep "Executing: python3 html_converter.py"
            if python3 "$SCRIPT_DIR/html_converter.py" -i "$input_path" -o "$html_output"; then
                print_success "Conversion completed successfully"
            else
                print_error "Conversion failed"
                rm -rf "$temp_extract_dir"
                exit 1
            fi
            
            # Cleanup
            if ! $NO_CLEANUP; then
                rm -rf "$temp_extract_dir"
            fi
            
        else
            # Input is already a directory or file
            local html_file="$INPUT"
            if [ -d "$INPUT" ]; then
                html_file=$(find "$INPUT" -name "*.html" | head -n 1)
            fi
            
            local manual_name=$(basename "$html_file" .html)
            local html_output="$OUTPUT/$manual_name"
            
            print_substep "Executing: python3 html_converter.py"
            if python3 "$SCRIPT_DIR/html_converter.py" -i "$html_file" -o "$html_output"; then
                print_success "Conversion completed successfully"
            else
                print_error "Conversion failed"
                exit 1
            fi
        fi
        
    else
        # VLP Converter (Default)
        local converter_cmd="python3 \"$SCRIPT_DIR/vlp_converter.py\" -i \"$INPUT\" -o \"$OUTPUT\""
        
        if $VERBOSE; then
            converter_cmd="$converter_cmd -v"
        fi
        
        if $NO_CLEANUP; then
            converter_cmd="$converter_cmd --no-cleanup"
        fi
        
        print_step 1 2 "Converting VLP content to ScreenSteps format"
        print_substep "Executing: python3 vlp_converter.py"
        
        # Execute the converter command
        if eval "$converter_cmd"; then
            print_success "Conversion completed successfully"
        else
            print_error "Conversion failed"
            exit 1
        fi
    fi
    
    # Upload if requested
    if $UPLOAD; then
        print_step 2 2 "Uploading to ScreenSteps"
        
        # Find the converted content directory
        local content_dir
        if [ -f "$INPUT" ]; then
            # Extract manual name from ZIP
            content_dir="$OUTPUT/$(basename "$INPUT" .zip)"
        else
            content_dir="$OUTPUT/$(basename "$INPUT")"
        fi
        
        # Find actual content directory (may have different name)
        # This logic is error-prone. Instead, the python converter should return the actual path
        # or the bash script should parse the python converter's output.
        # For now, we will assume the output structure is consistent.
        if [ ! -d "$content_dir" ]; then
            content_dir=$(find "$OUTPUT" -maxdepth 1 -type d ! -name "$(basename "$OUTPUT")" -print -quit)
        fi
        
        if [ -z "$content_dir" ] || [ ! -d "$content_dir" ]; then
            print_error "Could not find converted content directory"
            exit 1
        fi
        
        print_substep "Content directory: $content_dir"
        
        local upload_cmd="python3 \"$SCRIPT_DIR/screensteps_uploader.py\" \
            --content \"$content_dir\" \
            --account \"$ACCOUNT\" \
            --user \"$USER\" \
            --token \"$TOKEN\" \
            --site \"$SITE\""
        
        if $VERBOSE; then
            upload_cmd="$upload_cmd -v"
        fi

        if [ -n "$SUFFIX_FLAG" ]; then
            upload_cmd="$upload_cmd $SUFFIX_FLAG"
        fi
        
        if eval "$upload_cmd"; then
            print_success "Upload completed successfully"
        else
            print_error "Upload failed"
            exit 1
        fi
    fi
    
    print_header "Process Complete!"
    print_success "All operations completed successfully"
    print_info "Output location: $OUTPUT"
}

################################################################################
# Main Script
################################################################################

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input)
                INPUT="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                VERBOSE_FLAG="-v" # Set flag for uploader
                shift
                ;;
            --no-cleanup)
                NO_CLEANUP=true
                shift
                ;;
            --upload)
                UPLOAD=true
                shift
                ;;
            --account)
                ACCOUNT="$2"
                shift 2
                ;;
            --user)
                USER="$2"
                shift 2
                ;;
            --token)
                TOKEN="$2"
                shift 2
                ;;
            --site)
                SITE="$2"
                shift 2
                ;;
            --suffix)
                SUFFIX_FLAG="--suffix"
                shift # past argument
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                print_usage
                exit 0
                ;;
            --examples)
                python3 "$SCRIPT_DIR/vlp_converter.py" --examples
                exit 0
                ;;
            --version)
                python3 "$SCRIPT_DIR/vlp_converter.py" --version
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
    
    # Show usage if no arguments
    if [ $# -eq 0 ] && [ -z "$INPUT" ]; then
        print_usage
        echo ""
        print_info "Run with --examples to see detailed usage examples"
        exit 0
    fi
    
    # Check dependencies
    check_dependencies
    
    # Validate input
    validate_input
    
    # Run conversion
    run_conversion
}

# Execute main function
main "$@"
