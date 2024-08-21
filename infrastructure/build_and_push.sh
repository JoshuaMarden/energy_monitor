# Dockerises modules and pushes to AWS

# This ONLY runs if executed from INSIDE infrastructure/

# Docker can only see files in subdirectories. Therefore all the
# files used are imported to a temporarily created 'build_context' dir.
# Then the script logs into AWS, dockerises modules, pushes them to AWS ECRs.
# This build directory is cleaned up at the end.
# Purely for my personal interest, the script also times itself.

# Variables
REGION="eu-west-2"
ACCOUNT_ID="129033205317"
CLUSTER_NAME="c12-cluster"
SERVICE_NAME="c12-energy-dashboard"
REPO_PREFIX="c12-energy"
REPO_SUFFIX=("extract" "extract-carbon" "pipeline" "dashboard")
IMAGE_NAMES=("extract_to_s3" "extract_carbon" "transform_load" "dashboard")
DOCKERFILES=("Dockerfile.extract_many" "Dockerfile.extract_carbon" "Dockerfile.transform_load" "Dockerfile.dashboard")
ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
PLATFORM="linux/amd64"
BUILD_DIR="build_context"

# List of files and directories to copy into the build directory
FILES_TO_COPY=(
    "../pipeline"
    "../dashboard"
    "../config.py"
    "../constants.py"
    "../requirements.txt"
    "Dockerfile.*"
)

# Time the main script execution
time (
    # Create repositories (if they don't already exist)
    for SUFFIX in "${REPO_SUFFIX[@]}"; do
        aws ecr create-repository --repository-name "${REPO_PREFIX}-${SUFFIX}" --region $REGION || echo "Repository ${REPO_PREFIX}-${SUFFIX} already exists."
    done

    # Login to Aamazon AWS ECR.
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URL

    # Create a temporary build directory to house build files.
    mkdir -p $BUILD_DIR

    # Copy all necessary files used by docker into the new build directory.
    for FILE in "${FILES_TO_COPY[@]}"; do
        cp -r $FILE $BUILD_DIR/
    done

    # Containerise and push >>> ECR
    for i in "${!IMAGE_NAMES[@]}"; do

        IMAGE_NAME="${IMAGE_NAMES[$i]}"
        DOCKERFILE="${DOCKERFILES[$i]}"
        REPO_NAME="${REPO_PREFIX}-${REPO_SUFFIX[$i]}"

        docker build -t ${IMAGE_NAME}:latest -f ${BUILD_DIR}/${DOCKERFILE} --platform ${PLATFORM} ${BUILD_DIR}/
        docker tag ${IMAGE_NAME}:latest ${ECR_URL}/${REPO_NAME}:latest
        docker push ${ECR_URL}/${REPO_NAME}:latest
    done

    # Clean up the build directory.
    rm -rf $BUILD_DIR

    aws ecs update-service --cluster ${CLUSTER_NAME} --service ${SERVICE_NAME} --force-new-deployment
)
# Will hopefully print execution time now.