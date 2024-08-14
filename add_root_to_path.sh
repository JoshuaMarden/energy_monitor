# Determine the project root (current directory)
PROJECT_ROOT=$(pwd)

# Determine the virtual environment's site-packages directory
# First, check if the virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
  echo "No virtual environment detected. Please activate your virtual environment and run the script again."
  exit 1
fi

# Construct the path to the site-packages directory
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
VENV_SITE_PACKAGES="$VIRTUAL_ENV/lib/python$PYTHON_VERSION/site-packages"

# Define the name of the .pth file to be created
PTH_FILE="project_root.pth"

# Create the .pth file with the path to the project root
echo "$PROJECT_ROOT" > "$VENV_SITE_PACKAGES/$PTH_FILE"

# Provide feedback to the user
if [ $? -eq 0 ]; then
  echo ".pth file created successfully at $VENV_SITE_PACKAGES/$PTH_FILE"
  echo "Project root path $PROJECT_ROOT has been added to the .pth file."
else
  echo "An error occurred while creating the .pth file."
fi