#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal encoding fix for all platforms
Import this at the beginning of any Python script to fix encoding issues
"""

import os
import sys

# SAVE ORIGINAL PRINT FIRST, BEFORE ANY OVERRIDES
import builtins
_ORIGINAL_PRINT = builtins.print

def apply_universal_encoding_fix():
    """
    Triệt để fix encoding issues cho tất cả platforms
    """
    try:
        # 1. Environment variables - tất cả encoding-related
        encoding_vars = {
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONLEGACYWINDOWSSTDIO': '1',
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8',
            'LC_CTYPE': 'en_US.UTF-8',
        }
        
        for key, value in encoding_vars.items():
            os.environ[key] = value
        
        # 2. Windows specific - chcp + console encoding
        if sys.platform.startswith('win'):
            try:
                # Set console code page to UTF-8
                os.system('chcp 65001 >nul 2>&1')
                
                # Try to set console output to UTF-8
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleOutputCP(65001)
                kernel32.SetConsoleCP(65001)
            except:
                pass
        
        # 3. Reconfigure sys streams với error handling
        streams = [sys.stdout, sys.stderr, sys.stdin]
        for stream in streams:
            if hasattr(stream, 'reconfigure'):
                try:
                    stream.reconfigure(encoding='utf-8', errors='replace')
                except:
                    pass
        
        # 4. Set locale
        try:
            import locale
            # Try different UTF-8 locales
            utf8_locales = ['C.UTF-8', 'en_US.UTF-8', 'UTF-8']
            for loc in utf8_locales:
                try:
                    locale.setlocale(locale.LC_ALL, loc)
                    break
                except:
                    continue
        except:
            pass
            
        # 5. Set default file encoding for open()
        try:
            import codecs
            # This affects default encoding for file operations
            codecs.register_error('replace_with_warning', lambda e: ('?', e.end))
        except:
            pass
            
        return True
        
    except Exception:
        return False

# Apply immediately when imported
apply_universal_encoding_fix()

def safe_print(*args, **kwargs):
    """
    Universal safe print function - ALWAYS use original print to avoid recursion
    """
    try:
        _ORIGINAL_PRINT(*args, **kwargs)  # Use saved original print
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Emoji replacements
        emoji_map = {
            '🚀': '[START]', '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARNING]',
            '📝': '[NOTE]', '🔍': '[SEARCH]', '💰': '[CREDITS]', '🎨': '[GENERATE]',
            '📐': '[RATIO]', '🖼️': '[IMAGE]', '📁': '[FOLDER]', '⏳': '[WAIT]',
            '🌐': '[WEB]', '🔥': '[FIRE]', '🎯': '[TARGET]', '🤔': '[THINK]',
            '🎉': '[PARTY]', '🔧': '[TOOL]', '🐍': '[PYTHON]', '💾': '[SAVE]',
            '📊': '[CHART]', '🔄': '[RELOAD]', '📋': '[COPY]', '⭐': '[STAR]'
        }
        
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_arg = arg
                for emoji, replacement in emoji_map.items():
                    safe_arg = safe_arg.replace(emoji, replacement)
                safe_args.append(safe_arg)
            else:
                try:
                    safe_args.append(str(arg))
                except:
                    safe_args.append('[UNPRINTABLE]')
        
        try:
            _ORIGINAL_PRINT(*safe_args, **kwargs)  # Use original print always
        except:
            _ORIGINAL_PRINT("Output contains characters that cannot be displayed", **kwargs)

# Export the safe print
__all__ = ['apply_universal_encoding_fix', 'safe_print']
