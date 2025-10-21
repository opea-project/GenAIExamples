#!/usr/bin/env python3
"""
Simple test script to verify MSmartCompute Engine build
"""

import os
import sys
import subprocess
import platform

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_dependencies():
    """Check if required dependencies are available"""
    print("Checking dependencies...")
    
    dependencies = {
        'cmake': 'cmake --version',
        'python': 'python --version',
        'pip': 'pip --version',
        'git': 'git --version'
    }
    
    if platform.system() == "Windows":
        dependencies['nvcc'] = 'nvcc --version'
    else:
        dependencies['nvcc'] = 'nvcc --version'
    
    missing = []
    for name, cmd in dependencies.items():
        success, stdout, stderr = run_command(cmd)
        if success:
            print(f"✓ {name}: {stdout.strip()}")
        else:
            print(f"✗ {name}: Not found")
            missing.append(name)
    
    return missing

def check_cmake_config():
    """Check if CMake can configure the project"""
    print("\nTesting CMake configuration...")
    
    # Create build directory
    build_dir = "build_test"
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    
    # Try to configure
    cmake_cmd = "cmake .. -DCMAKE_BUILD_TYPE=Release"
    if platform.system() == "Windows":
        cmake_cmd += ' -G "Visual Studio 16 2019" -A x64'
        if os.path.exists("C:\\vcpkg\\scripts\\buildsystems\\vcpkg.cmake"):
            cmake_cmd += ' -DCMAKE_TOOLCHAIN_FILE="C:\\vcpkg\\scripts\\buildsystems\\vcpkg.cmake"'
    
    success, stdout, stderr = run_command(cmake_cmd, cwd=build_dir)
    
    if success:
        print("✓ CMake configuration successful")
        return True
    else:
        print("✗ CMake configuration failed")
        print("Error:", stderr)
        return False

def check_python_dependencies():
    """Check if Python dependencies are available"""
    print("\nChecking Python dependencies...")
    
    required_packages = [
        'numpy', 'torch', 'pybind11', 'streamlit', 'pandas', 
        'plotly', 'requests', 'pydantic', 'python-dateutil'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package}")
            missing.append(package)
    
    return missing

def main():
    print("MSmartCompute Engine Build Test")
    print("=" * 40)
    
    # Check system info
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python: {sys.version}")
    
    # Check dependencies
    missing_deps = check_dependencies()
    
    # Check Python dependencies
    missing_python = check_python_dependencies()
    
    # Test CMake configuration
    cmake_ok = check_cmake_config()
    
    # Summary
    print("\n" + "=" * 40)
    print("BUILD TEST SUMMARY")
    print("=" * 40)
    
    if missing_deps:
        print(f"✗ Missing system dependencies: {', '.join(missing_deps)}")
    else:
        print("✓ All system dependencies found")
    
    if missing_python:
        print(f"✗ Missing Python packages: {', '.join(missing_python)}")
        print("  Install with: pip install " + " ".join(missing_python))
    else:
        print("✓ All Python dependencies found")
    
    if cmake_ok:
        print("✓ CMake configuration successful")
        print("\n🎉 Build environment is ready!")
        print("You can now run the build scripts:")
        if platform.system() == "Windows":
            print("  setup.bat")
        else:
            print("  ./setup.sh")
    else:
        print("✗ CMake configuration failed")
        print("Please check the error messages above and install missing dependencies")
    
    # Cleanup
    if os.path.exists("build_test"):
        import shutil
        shutil.rmtree("build_test")

if __name__ == "__main__":
    main() 