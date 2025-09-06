#!/bin/bash

BUILD_DIR="build"
INSTALL_DIR="install"
CONFIG_DIR="config"
MODELS_DIR="models"
RESOURCES_DIR="resources"

echo "Building Smart Surveillance System..."

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning previous build..."
    rm -rf $BUILD_DIR
fi

# Create build directory
mkdir -p $BUILD_DIR
cd $BUILD_DIR

# Run CMake
echo "Running CMake..."
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=../$INSTALL_DIR \
      -DOPENCV_DIR=/usr/local/opencv \
      ..

# Check if CMake succeeded
if [ $? -ne 0 ]; then
    echo "CMake configuration failed!"
    exit 1
fi

# Compile system
echo "Compiling system..."
make -j$(nproc)

# Check if compilation succeeded
if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

# Install system
echo "Installing system..."
make install

# Copy configuration files and resources
echo "Copying configuration files..."
cd ..
mkdir -p $INSTALL_DIR/config
mkdir -p $INSTALL_DIR/models
mkdir -p $INSTALL_DIR/resources

cp -r $CONFIG_DIR/* $INSTALL_DIR/config/
cp -r $MODELS_DIR/* $INSTALL_DIR/models/
cp -r $RESOURCES_DIR/* $INSTALL_DIR/resources/

# Create run script
echo "Creating run script..."
cat > $INSTALL_DIR/run_system.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./bin/smart_surveillance_system
EOF

chmod +x $INSTALL_DIR/run_system.sh

echo "Build completed successfully!"
echo "Installation directory: $INSTALL_DIR"
echo "To run the system: cd $INSTALL_DIR && ./run_system.sh"

# Display system information
echo "System information:"
echo "  Build type: Release"
echo "  Installation prefix: $(pwd)/$INSTALL_DIR"
echo "  Binary path: $(pwd)/$INSTALL_DIR/bin/smart_surveillance_system"