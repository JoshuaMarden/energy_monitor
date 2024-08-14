# Get the current directory
DIR=$(pwd)

# Find and delete all .log and .prof files
find "$DIR" -type f \( -name "*.log" -o -name "*.prof" \) -exec rm -f {} \;

# Print completion message
echo "All .log and .prof files in the current- and sub-dirs have been deleted."
