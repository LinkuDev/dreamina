#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Multi-Instance Launcher for Dreamina
Chỉ cần 1 file .env để config tất cả
"""

import os
import subprocess
import threading
import time
import sys
import shutil
from pathlib import Path

# Fix Windows console encoding
if sys.platform.startswith('win'):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):  
            sys.stderr.reconfigure(encoding='utf-8')
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

# Safe print function
def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)  # Use original print, not overridden one
    except UnicodeEncodeError:
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_arg = (arg.replace('🚀', '[START]')
                              .replace('✅', '[OK]')
                              .replace('❌', '[ERROR]')
                              .replace('⚠️', '[WARNING]')
                              .replace('📝', '[NOTE]')
                              .replace('🔍', '[SEARCH]')
                              .replace('💰', '[CREDITS]')
                              .replace('🎨', '[GENERATE]')
                              .replace('📐', '[RATIO]')
                              .replace('🖼️', '[IMAGE]')
                              .replace('📁', '[FOLDER]')
                              .replace('⏳', '[WAIT]')
                              .replace('🌐', '[WEB]')
                              .replace('🔥', '[FIRE]')
                              .replace('🎯', '[TARGET]')
                              .replace('🤔', '[THINK]')
                              .replace('🎉', '[PARTY]')
                              .replace('🔧', '[TOOL]')
                              .replace('🐍', '[PYTHON]'))
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        _original_print(*safe_args, **kwargs)  # Use original print

# Store original print BEFORE defining safe_print
import builtins
_original_print = builtins.print
# Override print for this script
print = safe_print

class SimpleLauncher:
    def __init__(self):
        self.workspace = Path(__file__).parent
        self.env_file = self.workspace / ".env"
        self.instances = []
        self.python_cmd = self.detect_python_command()
        
    def detect_python_command(self):
        """Detect available Python command"""
        import platform
        
        # For Windows, try these commands in order
        if platform.system() == "Windows":
            commands = ['python', 'py', 'python3']
        else:
            commands = ['python3', 'python', 'py']
        
        for cmd in commands:
            if shutil.which(cmd):
                try:
                    # Test if command works
                    result = subprocess.run([cmd, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and 'Python' in result.stdout:
                        print(f"🐍 Detected Python: {cmd} ({result.stdout.strip()})")
                        return cmd
                except Exception as e:
                    print(f"⚠️  {cmd} test failed: {e}")
                    continue
        
        # Last resort: try sys.executable
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"🐍 Using sys.executable: {sys.executable}")
                return sys.executable
        except:
            pass
        
        # Ultimate fallback
        print(f"❌ No working Python found, will try 'python'")
        return 'python'
        
    def load_config(self):
        """Load config từ .env file duy nhất"""
        config = {}
        
        if not self.env_file.exists():
            # Tạo .env mẫu
            self.create_sample_env()
            
        with open(self.env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        return config
    
    def create_sample_env(self):
        """Tạo file .env mẫu"""
        sample_content = '''# Simple Multi-Instance Config for Dreamina
# Cấu hình đơn giản cho việc chạy song song

# Số lượng instances muốn chạy
INSTANCES=3

# Thư mục cookies (sẽ auto tạo cookies1, cookies2, cookies3...)
COOKIES_BASE=cookies

# File prompts (sẽ auto tạo prompts1.txt, prompts2.txt, prompts3.txt...)
PROMPTS_BASE=prompts

# Thư mục output (sẽ auto tạo outputs1, outputs2, outputs3...)
OUTPUTS_BASE=outputs

# Aspect ratio cho tất cả instances
ASPECT_RATIO=16:9

# Số ảnh per prompt
IMAGE_COUNT=4

# Chạy ẩn browser (true/false)
BROWSER_HEADLESS=false

# Delay giữa các instances (seconds)
STARTUP_DELAY=5
'''
        
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        
        print(f"📝 Created sample .env at: {self.env_file}")
        print("📝 Edit .env file and run again!")
        return False
        
    def validate_configuration(self, config):
        """
        Strict validation của configuration
        Stop và báo lỗi rõ ràng nếu thiếu gì
        """
        errors = []
        instances_count = int(config.get('INSTANCES', 3))
        cookies_base = config.get('COOKIES_BASE', 'cookies')
        
        # 1. Validate ASPECT_RATIO
        aspect_ratios_str = config.get('ASPECT_RATIO', '')
        if not aspect_ratios_str:
            errors.append("❌ ASPECT_RATIO is empty in .env file")
        else:
            aspect_ratios = [ratio.strip() for ratio in aspect_ratios_str.split(',')]
            if len(aspect_ratios) != instances_count:
                errors.append(f"❌ ASPECT_RATIO has {len(aspect_ratios)} ratios but INSTANCES={instances_count}")
                errors.append(f"   Current: {aspect_ratios}")
                errors.append(f"   Required: Must have exactly {instances_count} ratios")
        
        # 2. Validate cookies folders
        for i in range(1, instances_count + 1):
            cookies_dir = self.workspace / f"{cookies_base}{i}"
            if not cookies_dir.exists():
                errors.append(f"❌ Missing cookies folder: {cookies_dir}")
            else:
                cookie_files = list(cookies_dir.glob("*.json"))
                if len(cookie_files) == 0:
                    errors.append(f"❌ Empty cookies folder: {cookies_dir}")
        
        # 3. Validate prompt files
        for i in range(1, instances_count + 1):
            prompt_file = self.workspace / "prompts" / f"{i}.txt"
            if not prompt_file.exists():
                errors.append(f"❌ Missing prompt file: {prompt_file}")
            else:
                # Check if file has content
                try:
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if not content:
                            errors.append(f"❌ Empty prompt file: {prompt_file}")
                except Exception as e:
                    errors.append(f"❌ Cannot read prompt file {prompt_file}: {e}")
        
        # 4. Print results
        if errors:
            print("\n🔥 VALIDATION FAILED!")
            print("=" * 60)
            for error in errors:
                print(error)
            print("=" * 60)
            print("\n💡 Fix these issues:")
            print(f"   1. Create missing cookies folders: cookies1, cookies2, ..., cookies{instances_count}")
            print(f"   2. Create missing prompt files: prompts/1.txt, prompts/2.txt, ..., prompts/{instances_count}.txt")
            print(f"   3. Set ASPECT_RATIO with {instances_count} ratios (e.g., 16:9,1:1,9:16)")
            return False
        
        print("\n✅ VALIDATION PASSED!")
        print("=" * 50)
        print(f"   ✅ {instances_count} instances configured")
        print(f"   ✅ {instances_count} cookies folders found")
        print(f"   ✅ {instances_count} prompt files found")
        print(f"   ✅ {len(aspect_ratios)} aspect ratios configured")
        return True
    
    def setup_directories(self, config):
        """Setup thư mục cho từng instance - chỉ tạo outputs, không tạo cookies/prompts"""
        instances_count = int(config.get('INSTANCES', 3))
        outputs_base = config.get('OUTPUTS_BASE', 'outputs')
        
        # Chỉ tạo thư mục outputs (cookies và prompts phải tồn tại rồi)
        for i in range(1, instances_count + 1):
            outputs_dir = self.workspace / f"{outputs_base}{i}"
            outputs_dir.mkdir(exist_ok=True)
            
        return instances_count
    
    def get_aspect_ratio_for_worker(self, worker_id, aspect_ratios):
        """Get aspect ratio cho worker theo index (bắt đầu từ 0)"""
        ratio_index = (worker_id - 1) % len(aspect_ratios)
        return aspect_ratios[ratio_index]
    
    def run_instance(self, instance_id, config):
        """Chạy 1 instance với config riêng và aspect ratio rotation"""
        cookies_base = config.get('COOKIES_BASE', 'cookies')
        outputs_base = config.get('OUTPUTS_BASE', 'outputs')
        
        # Parse aspect ratios
        aspect_ratios_str = config.get('ASPECT_RATIO', '16:9')
        aspect_ratios = [ratio.strip() for ratio in aspect_ratios_str.split(',')]
        
        # Get aspect ratio for this worker
        worker_aspect_ratio = self.get_aspect_ratio_for_worker(instance_id, aspect_ratios)
        
        # Set environment variables cho instance này
        env = os.environ.copy()
        env.update({
            'COOKIES_FOLDER': f"{cookies_base}{instance_id}",
            'PROMPT_FILE': f"prompts/{instance_id}.txt",  # Changed to {id}.txt
            'OUTPUT_DIR': f"{outputs_base}{instance_id}",
            'ASPECT_RATIO': worker_aspect_ratio,  # Single ratio for this worker
            'IMAGE_COUNT': config.get('IMAGE_COUNT', '4'),
            'BROWSER_HEADLESS': config.get('BROWSER_HEADLESS', 'false')
        })
        
        print(f"🚀 Starting worker{instance_id}...")
        print(f"   📁 Cookies: {env['COOKIES_FOLDER']}")
        print(f"   📝 Prompts: {env['PROMPT_FILE']}")
        print(f"   📐 Aspect Ratio: {worker_aspect_ratio}")
        print(f"   💾 Output: {env['OUTPUT_DIR']}")
        
        try:
            # Debug: Show exact command being run
            cmd_str = f"{self.python_cmd} main.py"
            print(f"   🔧 Command: {cmd_str}")
            print(f"   📁 Working dir: {self.workspace}")
            
            # Chạy main.py với environment variables
            result = subprocess.run(
                [self.python_cmd, 'main.py'],
                cwd=self.workspace,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"✅ worker{instance_id} completed successfully")
                if result.stdout:
                    print(f"📝 worker{instance_id} stdout:\n{result.stdout}")
            else:
                print(f"❌ worker{instance_id} failed with code: {result.returncode}")
                print(f"📝 worker{instance_id} stderr:\n{result.stderr}")
                if result.stdout:
                    print(f"📝 worker{instance_id} stdout:\n{result.stdout}")
                
        except subprocess.TimeoutExpired:
            print(f"❌ worker{instance_id} timeout (5 minutes)")
        except FileNotFoundError as e:
            print(f"❌ worker{instance_id} command not found: {e}")
            print(f"   💡 Try installing Python or check PATH")
        except Exception as e:
            print(f"❌ worker{instance_id} error: {e}")
    
    def launch(self):
        """Launch tất cả instances với strict validation"""
        print("🔥 Simple Dreamina Multi-Instance Launcher")
        print("=" * 50)
        
        # Load config
        config = self.load_config()
        if not config:
            return
        
        # Strict validation
        if not self.validate_configuration(config):
            return
        
        # Setup directories (only outputs)
        instances_count = self.setup_directories(config)
        startup_delay = int(config.get('STARTUP_DELAY', 5))
        
        print(f"\n🎯 Ready to launch {instances_count} instances...")
        print(f"⏰ Startup delay: {startup_delay}s between instances")
        
        # Show aspect ratio mapping
        aspect_ratios_str = config.get('ASPECT_RATIO', '16:9')
        aspect_ratios = [ratio.strip() for ratio in aspect_ratios_str.split(',')]
        print(f"📐 Aspect Ratio Mapping:")
        for i in range(1, instances_count + 1):
            worker_ratio = self.get_aspect_ratio_for_worker(i, aspect_ratios)
            print(f"   Worker{i} → {worker_ratio}")
        
        # Confirm
        confirm = input("\n🤔 Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return
        
        # Launch instances
        threads = []
        for i in range(1, instances_count + 1):
            if i > 1:
                print(f"⏰ Waiting {startup_delay}s before starting worker{i}...")
                time.sleep(startup_delay)
            
            thread = threading.Thread(
                target=self.run_instance,
                args=(i, config),
                daemon=True
            )
            thread.start()
            threads.append(thread)
        
        # Wait for all
        print("⏳ Waiting for all instances to complete...")
        for thread in threads:
            thread.join()
        
        print("🎉 All instances completed!")

if __name__ == "__main__":
    launcher = SimpleLauncher()
    launcher.launch()
