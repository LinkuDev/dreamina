#!/usr/bin/env python3
"""
Test script để kiểm tra Python detection và file paths
"""
import subprocess
import sys
import platform
from pathlib import Path

def test_python_detection():
    print("🔍 Testing Python Detection")
    print("=" * 50)
    
    print(f"🖥️  Platform: {platform.system()}")
    print(f"🐍 sys.executable: {sys.executable}")
    
    commands = ['python', 'py', 'python3']
    
    for cmd in commands:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            status = "✅" if result.returncode == 0 else "❌"
            print(f"   {status} {cmd}: {result.stdout.strip() if result.stdout else result.stderr.strip()}")
        except Exception as e:
            print(f"   ❌ {cmd}: Error - {e}")

def test_files():
    print("\n📁 Testing File Structure")
    print("=" * 50)
    
    workspace = Path(__file__).parent
    
    # Check .env
    env_file = workspace / ".env"
    print(f"   {'✅' if env_file.exists() else '❌'} .env: {env_file}")
    
    # Check for 3 instances
    for i in range(1, 4):
        cookies_dir = workspace / f"cookies{i}"
        prompt_file = workspace / "prompts" / f"{i}.txt"
        output_dir = workspace / f"outputs{i}"
        
        print(f"   {'✅' if cookies_dir.exists() else '❌'} cookies{i}: {cookies_dir}")
        print(f"   {'✅' if prompt_file.exists() else '❌'} prompts/{i}.txt: {prompt_file}")
        print(f"   {'✅' if output_dir.exists() else '❌'} outputs{i}: {output_dir}")

if __name__ == "__main__":
    print("🧪 DREAMINA SETUP TEST")
    print("=" * 60)
    test_python_detection()
    test_files()
    print("\n✅ Test completed!")
