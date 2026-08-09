export EASYAIOT_DEPLOY_PROFILE=full
export EASYAIOT_SKIP_PROFILE_PROMPT=1
export EASYAIOT_SKIP_IMAGE_PROMPT=1
export EASYAIOT_SKIP_BUILD=1
export EASYAIOT_FORCE_WINDOWS=1
cd /f/acme
bash .scripts/docker/install_windows.sh install
